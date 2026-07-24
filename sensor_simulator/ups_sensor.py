"""UPS battery sensor used by the simulator."""

from __future__ import annotations

from sensor_simulator.base_sensor import BaseSensor
from shared.models import SensorType


class UPSBatterySensor(BaseSensor):
    def __init__(self) -> None:
        super().__init__(
            sensor_type=SensorType.UPS,
            unit="%",
            baseline=98.0,
            volatility=0.3,
            minimum=5.0,
            maximum=100.0,
            drift=0.0,
            anomaly_spike=0.0,
            anomaly_drop=25.0,
        )
