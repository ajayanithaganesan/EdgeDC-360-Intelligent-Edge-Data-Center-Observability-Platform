"""Humidity sensor used by the simulator."""

from __future__ import annotations

from sensor_simulator.base_sensor import BaseSensor
from shared.models import SensorType


class HumiditySensor(BaseSensor):
    def __init__(self) -> None:
        super().__init__(
            sensor_type=SensorType.HUMIDITY,
            unit="%",
            baseline=45.0,
            volatility=0.8,
            minimum=18.0,
            maximum=88.0,
            drift=0.0,
            anomaly_spike=18.0,
            anomaly_drop=10.0,
        )
