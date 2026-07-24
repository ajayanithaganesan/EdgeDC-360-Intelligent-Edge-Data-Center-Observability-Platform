"""Cooling sensor used by the simulator."""

from __future__ import annotations

from sensor_simulator.base_sensor import BaseSensor
from shared.models import SensorType


class CoolingSensor(BaseSensor):
    def __init__(self) -> None:
        super().__init__(
            sensor_type=SensorType.COOLING,
            unit="RPM",
            baseline=2250.0,
            volatility=25.0,
            minimum=400.0,
            maximum=4200.0,
            drift=0.0,
            anomaly_spike=400.0,
            anomaly_drop=1100.0,
        )
