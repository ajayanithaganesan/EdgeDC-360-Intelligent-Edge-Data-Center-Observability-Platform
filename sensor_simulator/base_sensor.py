"""Base logic shared by the simple sensor modules."""

from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Optional

from shared.models import SensorType


@dataclass(slots=True)
class BaseSensor:
    sensor_type: SensorType
    unit: str
    baseline: float
    volatility: float
    minimum: float
    maximum: float
    drift: float = 0.0
    anomaly_spike: float = 0.0
    anomaly_drop: float = 0.0

    def generate(self, rng: Optional[Random], previous: float, anomaly_rate: float) -> tuple[float, bool]:
        if rng is None:
            rng = Random(0)

        # Pull value back towards baseline (mean reversion) to stay safely in normal range
        reversion = 0.25 * (self.baseline - previous)
        value = previous + reversion + rng.uniform(-self.volatility, self.volatility) + self.drift
        
        anomaly = rng.random() < anomaly_rate
        if anomaly:
            if rng.random() < 0.5 and self.anomaly_spike:
                value += self.anomaly_spike * rng.uniform(0.5, 1.0)
            elif self.anomaly_drop:
                value -= self.anomaly_drop * rng.uniform(0.5, 1.0)

        return max(self.minimum, min(self.maximum, value)), anomaly
