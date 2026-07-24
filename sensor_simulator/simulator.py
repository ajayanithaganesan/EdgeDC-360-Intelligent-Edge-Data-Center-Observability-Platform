"""Realistic sensor simulation for data center telemetry."""

from __future__ import annotations

from dataclasses import dataclass, field
from random import Random
from typing import Iterable

from sensor_simulator.cooling_sensor import CoolingSensor
from sensor_simulator.humidity_sensor import HumiditySensor
from sensor_simulator.power_sensor import PowerSensor
from sensor_simulator.temperature_sensor import TemperatureSensor
from sensor_simulator.ups_sensor import UPSBatterySensor
from shared.models import SensorReading, SensorType, utc_now


@dataclass(slots=True)
class RackSimulator:
    site: str
    rack_id: str
    seed: int
    anomaly_rate: float
    sequence: int = 0
    state: dict[SensorType, float] = field(init=False)
    rng: Random = field(init=False, repr=False)
    sensors: list[object] = field(init=False)

    def __post_init__(self) -> None:
        self.rng = Random(self.seed)
        self.sensors = [
            TemperatureSensor(),
            HumiditySensor(),
            PowerSensor(),
            UPSBatterySensor(),
            CoolingSensor(),
        ]
        self.state = {sensor.sensor_type: sensor.baseline for sensor in self.sensors}

    def sample(self, timestamp: str | None = None) -> list[SensorReading]:
        timestamp = timestamp or utc_now()
        readings: list[SensorReading] = []
        self.sequence += 1
        for sensor in self.sensors:
            previous = self.state[sensor.sensor_type]
            value, anomaly = sensor.generate(self.rng, previous, self.anomaly_rate)
            self.state[sensor.sensor_type] = value
            readings.append(
                SensorReading(
                    timestamp=timestamp,
                    site=self.site,
                    rack_id=self.rack_id,
                    sensor_type=sensor.sensor_type,
                    value=round(value, 2),
                    unit=sensor.unit,
                    sequence=self.sequence,
                    anomaly=anomaly,
                    metadata={"source": "simulator"},
                )
            )
        return readings


class SensorSimulator:
    """Generate telemetry for every rack in every site."""

    def __init__(self, *, sites: Iterable[str], racks_per_site: int, seed: int, anomaly_rate: float) -> None:
        self.racks: list[RackSimulator] = []
        base_seed = seed
        for site_index, site in enumerate(sites):
            for rack_number in range(1, racks_per_site + 1):
                rack_seed = base_seed + site_index * 100 + rack_number
                self.racks.append(
                    RackSimulator(
                        site=site,
                        rack_id=f"rack-{rack_number:02d}",
                        seed=rack_seed,
                        anomaly_rate=anomaly_rate,
                    )
                )

    def sample_once(self) -> list[SensorReading]:
        readings: list[SensorReading] = []
        for rack in self.racks:
            readings.extend(rack.sample())
        return readings
