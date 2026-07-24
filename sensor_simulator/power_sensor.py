"""Power sensor used by the simulator."""

from __future__ import annotations

from sensor_simulator.base_sensor import BaseSensor
from shared.models import SensorType


class PowerSensor(BaseSensor):
    def __init__(self) -> None:
        super().__init__(
            sensor_type=SensorType.POWER,
            unit="W",
            baseline=400.0,
            volatility=8.0,
            minimum=150.0,
            maximum=1100.0,
            drift=0.0,
            anomaly_spike=240.0,
            anomaly_drop=70.0,
        )
