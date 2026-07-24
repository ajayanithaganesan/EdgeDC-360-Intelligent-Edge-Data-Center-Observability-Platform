"""Central configuration for EdgeDC360.

The project guide calls for environment-driven behaviour, so this module
keeps runtime settings in one place and avoids hardcoded values spread
through the codebase.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return default if value in (None, "") else int(value)


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return default if value in (None, "") else float(value)


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value in (None, ""):
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_str(name: str, default: str) -> str:
    value = os.getenv(name)
    return default if value in (None, "") else value


def _repo_root() -> Path:
    return Path(__file__).resolve().parent


@dataclass(slots=True)
class SensorConfig:
    sites: tuple[str, ...] = ("Dublin", "Cork", "Galway")
    racks_per_site: int = 2
    sample_interval_seconds: int = 5
    publish_interval_seconds: int = 30
    anomaly_rate: float = 0.0

    seed: int = 360


@dataclass(slots=True)
class GatewayThresholds:
    high_temperature_c: float = 30.0
    critical_temperature_c: float = 36.0
    high_humidity_pct: float = 65.0
    critical_humidity_pct: float = 80.0
    low_ups_pct: float = 35.0
    critical_ups_pct: float = 20.0
    high_power_watts: float = 600.0
    critical_power_watts: float = 750.0
    low_fan_rpm: float = 1400.0
    critical_fan_rpm: float = 900.0


@dataclass(slots=True)
class StorageConfig:
    sqlite_path: Path = field(default_factory=lambda: _repo_root() / "edge_gateway" / "edge_buffer.db")


@dataclass(slots=True)
class MQTTConfig:
    enabled: bool = False
    host: str = "localhost"
    port: int = 1883
    keepalive: int = 60
    username: str = ""
    password: str = ""
    sensor_topic_prefix: str = "edgedc360/sensors"
    gateway_topic_prefix: str = "edgedc360/gateway"
    client_id_prefix: str = "edgedc360"


@dataclass(slots=True)
class AppConfig:
    environment: str = "development"
    log_level: str = "INFO"
    sensor: SensorConfig = field(default_factory=SensorConfig)
    thresholds: GatewayThresholds = field(default_factory=GatewayThresholds)
    storage: StorageConfig = field(default_factory=StorageConfig)
    mqtt: MQTTConfig = field(default_factory=MQTTConfig)


def load_config() -> AppConfig:
    """Load runtime configuration from environment variables."""

    sensor = SensorConfig(
        sites=tuple(
            site.strip()
            for site in _env_str("EDGEDC360_SITES", "Dublin,Cork,Galway").split(",")
            if site.strip()
        ),
        racks_per_site=_env_int("EDGEDC360_RACKS_PER_SITE", 2),
        sample_interval_seconds=_env_int("EDGEDC360_SAMPLE_INTERVAL_SECONDS", 5),
        publish_interval_seconds=_env_int("EDGEDC360_PUBLISH_INTERVAL_SECONDS", 30),
        anomaly_rate=_env_float("EDGEDC360_ANOMALY_RATE", 0.0),

        seed=_env_int("EDGEDC360_SEED", 360),
    )

    thresholds = GatewayThresholds(
        high_temperature_c=_env_float("EDGEDC360_HIGH_TEMPERATURE_C", 30.0),
        critical_temperature_c=_env_float("EDGEDC360_CRITICAL_TEMPERATURE_C", 36.0),
        high_humidity_pct=_env_float("EDGEDC360_HIGH_HUMIDITY_PCT", 65.0),
        critical_humidity_pct=_env_float("EDGEDC360_CRITICAL_HUMIDITY_PCT", 80.0),
        low_ups_pct=_env_float("EDGEDC360_LOW_UPS_PCT", 35.0),
        critical_ups_pct=_env_float("EDGEDC360_CRITICAL_UPS_PCT", 20.0),
        high_power_watts=_env_float("EDGEDC360_HIGH_POWER_WATTS", 600.0),
        critical_power_watts=_env_float("EDGEDC360_CRITICAL_POWER_WATTS", 750.0),
        low_fan_rpm=_env_float("EDGEDC360_LOW_FAN_RPM", 1400.0),
        critical_fan_rpm=_env_float("EDGEDC360_CRITICAL_FAN_RPM", 900.0),
    )

    storage = StorageConfig(
        sqlite_path=Path(_env_str("EDGEDC360_SQLITE_PATH", str(_repo_root() / "edge_gateway" / "edge_buffer.db")))
    )

    mqtt = MQTTConfig(
        enabled=_env_bool("EDGEDC360_MQTT_ENABLED", False),
        host=_env_str("EDGEDC360_MQTT_HOST", "localhost"),
        port=_env_int("EDGEDC360_MQTT_PORT", 1883),
        keepalive=_env_int("EDGEDC360_MQTT_KEEPALIVE", 60),
        username=_env_str("EDGEDC360_MQTT_USERNAME", ""),
        password=_env_str("EDGEDC360_MQTT_PASSWORD", ""),
        sensor_topic_prefix=_env_str("EDGEDC360_SENSOR_TOPIC_PREFIX", "edgedc360/sensors"),
        gateway_topic_prefix=_env_str("EDGEDC360_GATEWAY_TOPIC_PREFIX", "edgedc360/gateway"),
        client_id_prefix=_env_str("EDGEDC360_MQTT_CLIENT_ID_PREFIX", "edgedc360"),
    )

    return AppConfig(
        environment=_env_str("EDGEDC360_ENV", "development"),
        log_level=_env_str("EDGEDC360_LOG_LEVEL", "INFO"),
        sensor=sensor,
        thresholds=thresholds,
        storage=storage,
        mqtt=mqtt,
    )
