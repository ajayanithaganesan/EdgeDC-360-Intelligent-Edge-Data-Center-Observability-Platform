"""Temperature sensor used by the simulator."""

from __future__ import annotations

from sensor_simulator.base_sensor import BaseSensor
from shared.models import SensorType


class TemperatureSensor(BaseSensor):
    def __init__(self) -> None:
        super().__init__(
            sensor_type=SensorType.TEMPERATURE,
            unit="C",
            baseline=22.5,
            volatility=0.4,
            minimum=16.0,
            maximum=48.0,
            drift=0.0,
            anomaly_spike=9.0,
            anomaly_drop=4.0,
        )
