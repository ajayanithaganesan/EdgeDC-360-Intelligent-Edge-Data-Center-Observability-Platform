"""Canonical telemetry models shared across simulator and gateway."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from statistics import pstdev
from typing import Any
import json
from datetime import datetime, timezone


class SensorType(str, Enum):
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    POWER = "power"
    UPS = "ups"
    COOLING = "cooling"


class DecisionType(str, Enum):
    FILTERED = "filtered"
    FORWARDED = "forwarded"
    ALERT = "alert"
    AGGREGATED = "aggregated"


class HealthState(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class SensorReading:
    timestamp: str
    site: str
    rack_id: str
    sensor_type: SensorType
    value: float
    unit: str
    sequence: int
    anomaly: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["sensor_type"] = self.sensor_type.value
        return payload

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), separators=(",", ":"))


@dataclass(slots=True)
class AggregatedReading:
    timestamp: str
    site: str
    rack_id: str
    sensor_type: SensorType
    count: int
    mean: float
    minimum: float
    maximum: float
    standard_deviation: float
    unit: str
    window_seconds: int

    @classmethod
    def from_values(
        cls,
        *,
        timestamp: str,
        site: str,
        rack_id: str,
        sensor_type: SensorType,
        values: list[float],
        unit: str,
        window_seconds: int,
    ) -> "AggregatedReading":
        if not values:
            raise ValueError("values must not be empty")
        count = len(values)
        mean = sum(values) / count
        minimum = min(values)
        maximum = max(values)
        standard_deviation = pstdev(values) if count > 1 else 0.0
        return cls(
            timestamp=timestamp,
            site=site,
            rack_id=rack_id,
            sensor_type=sensor_type,
            count=count,
            mean=mean,
            minimum=minimum,
            maximum=maximum,
            standard_deviation=standard_deviation,
            unit=unit,
            window_seconds=window_seconds,
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["sensor_type"] = self.sensor_type.value
        return payload


@dataclass(slots=True)
class GatewayDecision:
    timestamp: str
    reading: SensorReading
    decision: DecisionType
    reason: str
    health_score: int
    health_state: HealthState
    upload: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "reading": self.reading.to_dict(),
            "decision": self.decision.value,
            "reason": self.reason,
            "health_score": self.health_score,
            "health_state": self.health_state.value,
            "upload": self.upload,
        }


@dataclass(slots=True)
class RackHealthSnapshot:
    timestamp: str
    site: str
    rack_id: str
    health_score: int
    health_state: HealthState
    factors: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self) | {"health_state": self.health_state.value}


def reading_from_payload(payload: dict) -> SensorReading:
    """Deserialize a dictionary payload into a SensorReading model."""
    return SensorReading(
        timestamp=payload["timestamp"],
        site=payload["site"],
        rack_id=payload["rack_id"],
        sensor_type=SensorType(payload["sensor_type"]),
        value=float(payload["value"]),
        unit=payload["unit"],
        sequence=int(payload["sequence"]),
        anomaly=bool(payload.get("anomaly", False)),
        metadata=dict(payload.get("metadata", {})),
    )


def sensor_topic(prefix: str, reading: SensorReading) -> str:
    """Format MQTT topic string for a sensor reading."""
    return f"{prefix}/{reading.site}/{reading.rack_id}/{reading.sensor_type.value}"


def sensor_wildcard(prefix: str) -> str:
    """Format wildcard MQTT subscription topic."""
    return f"{prefix}/+/+/+"

