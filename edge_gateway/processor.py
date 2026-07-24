"""Edge processing logic for filtering, rules, aggregation, and health."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from statistics import mean
from typing import Iterable

from config import GatewayThresholds
from shared.models import (
    AggregatedReading,
    DecisionType,
    GatewayDecision,
    HealthState,
    RackHealthSnapshot,
    SensorReading,
    SensorType,
    utc_now,
)


@dataclass(slots=True)
class DuplicateFilter:
    last_seen: dict[tuple[str, str, str], float] = field(default_factory=dict)

    def is_duplicate(self, reading: SensorReading) -> bool:
        if reading.anomaly:
            return False
        key = (reading.site, reading.rack_id, reading.sensor_type.value)
        previous = self.last_seen.get(key)
        self.last_seen[key] = reading.value
        return previous is not None and abs(previous - reading.value) < 0.05


@dataclass(slots=True)
class RuleEngine:
    thresholds: GatewayThresholds

    def evaluate(self, reading: SensorReading) -> tuple[DecisionType, str]:
        value = reading.value
        if reading.sensor_type is SensorType.TEMPERATURE:
            if value >= self.thresholds.critical_temperature_c:
                return DecisionType.ALERT, "critical temperature"
            if value >= self.thresholds.high_temperature_c:
                return DecisionType.FORWARDED, "high temperature"
        if reading.sensor_type is SensorType.HUMIDITY:
            if value >= self.thresholds.critical_humidity_pct:
                return DecisionType.ALERT, "critical humidity"
            if value >= self.thresholds.high_humidity_pct:
                return DecisionType.FORWARDED, "high humidity"
        if reading.sensor_type is SensorType.POWER:
            if value >= self.thresholds.critical_power_watts:
                return DecisionType.ALERT, "power spike"
            if value >= self.thresholds.high_power_watts:
                return DecisionType.FORWARDED, "high power"
        if reading.sensor_type is SensorType.UPS:
            if value <= self.thresholds.critical_ups_pct:
                return DecisionType.ALERT, "critical ups level"
            if value <= self.thresholds.low_ups_pct:
                return DecisionType.FORWARDED, "low ups level"
        if reading.sensor_type is SensorType.COOLING:
            if value <= self.thresholds.critical_fan_rpm:
                return DecisionType.ALERT, "cooling failure"
            if value <= self.thresholds.low_fan_rpm:
                return DecisionType.FORWARDED, "cooling degradation"
        return DecisionType.FILTERED, "within nominal range"


@dataclass(slots=True)
class HealthScoreEngine:
    thresholds: GatewayThresholds

    def assess(self, readings: Iterable[SensorReading]) -> RackHealthSnapshot:
        readings = list(readings)
        if not readings:
            raise ValueError("readings must not be empty")
        values = {reading.sensor_type: reading.value for reading in readings}
        temp = values.get(SensorType.TEMPERATURE, 24.0)
        humidity = values.get(SensorType.HUMIDITY, 45.0)
        power = values.get(SensorType.POWER, 380.0)
        ups = values.get(SensorType.UPS, 90.0)
        cooling = values.get(SensorType.COOLING, 2200.0)

        score = 100.0
        score -= max(0.0, (temp - 24.0) * 2.4)
        score -= max(0.0, (humidity - 45.0) * 0.6)
        score -= max(0.0, (power - 380.0) / 18.0)
        score -= max(0.0, (2200.0 - cooling) / 40.0)
        score -= max(0.0, (92.0 - ups) * 1.7)
        score = max(0.0, min(100.0, score))

        if score >= 80:
            state = HealthState.HEALTHY
        elif score >= 55:
            state = HealthState.WARNING
        else:
            state = HealthState.CRITICAL

        first = readings[0]
        factors = {
            "temperature": temp,
            "humidity": humidity,
            "power": power,
            "ups": ups,
            "cooling": cooling,
        }
        return RackHealthSnapshot(
            timestamp=utc_now(),
            site=first.site,
            rack_id=first.rack_id,
            health_score=int(round(score)),
            health_state=state,
            factors=factors,
        )


@dataclass(slots=True)
class EdgeGatewayProcessor:
    thresholds: GatewayThresholds
    duplicate_filter: DuplicateFilter = field(default_factory=DuplicateFilter)
    rule_engine: RuleEngine = field(init=False)
    health_engine: HealthScoreEngine = field(init=False)
    window: dict[tuple[str, str], list[SensorReading]] = field(default_factory=dict)
    window_started_at: dict[tuple[str, str], datetime] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.rule_engine = RuleEngine(self.thresholds)
        self.health_engine = HealthScoreEngine(self.thresholds)

    def process(self, reading: SensorReading) -> GatewayDecision:
        if not self._is_valid(reading):
            return GatewayDecision(
                timestamp=utc_now(),
                reading=reading,
                decision=DecisionType.FILTERED,
                reason="invalid reading",
                health_score=0,
                health_state=HealthState.CRITICAL,
                upload=False,
            )

        if self.duplicate_filter.is_duplicate(reading):
            return GatewayDecision(
                timestamp=utc_now(),
                reading=reading,
                decision=DecisionType.FILTERED,
                reason="duplicate reading",
                health_score=100,
                health_state=HealthState.HEALTHY,
                upload=False,
            )

        decision, reason = self.rule_engine.evaluate(reading)
        rack_key = (reading.site, reading.rack_id)
        self.window.setdefault(rack_key, []).append(reading)
        if rack_key not in self.window_started_at:
            self.window_started_at[rack_key] = self._parse_timestamp(reading.timestamp)
        health = self.health_engine.assess(self.window[rack_key])

        upload = decision is not DecisionType.FILTERED
        return GatewayDecision(
            timestamp=utc_now(),
            reading=reading,
            decision=decision,
            reason=reason,
            health_score=health.health_score,
            health_state=health.health_state,
            upload=upload,
        )

    def process_and_flush(self, reading: SensorReading, *, batch_interval_seconds: int | None = None) -> tuple[GatewayDecision, AggregatedReading | None, dict | None]:
        """Process a reading and potentially flush batch aggregate. Returns (decision, agg_reading, cloud_payload)."""
        decision = self.process(reading)
        if batch_interval_seconds is None:
            return decision, None, None

        rack_key = (reading.site, reading.rack_id)
        current_window = self.window.get(rack_key, [])
        if not current_window:
            return decision, None, None

        if self._should_flush(current_window, reading.timestamp, batch_interval_seconds):
            agg, cloud = self.flush_aggregate(*rack_key)
            return decision, agg, cloud

        return decision, None, None

    def _should_flush(self, readings: list[SensorReading], current_timestamp: str, batch_interval_seconds: int) -> bool:
        if not readings:
            return False

        current_dt = self._parse_timestamp(current_timestamp)
        first_dt = self._parse_timestamp(readings[0].timestamp)
        return (current_dt - first_dt).total_seconds() >= batch_interval_seconds

    def summarize_rack(self, site: str, rack_id: str) -> RackHealthSnapshot | None:
        readings = self.window.get((site, rack_id), [])
        if not readings:
            return None
        return self.health_engine.assess(readings)

    def rack_aggregate_for_cloud(self, site: str, rack_id: str) -> dict | None:
        """Create a cloud-ready aggregated payload with all 5 sensors for a rack."""
        readings = self.window.get((site, rack_id), [])
        if not readings:
            return None
        return self._create_cloud_payload(readings, site, rack_id)

    def flush_due_aggregates(self, *, batch_interval_seconds: int, now: datetime | None = None) -> list[tuple[AggregatedReading, dict | None]]:
        if batch_interval_seconds <= 0:
            return []

        current_time = now or datetime.now(timezone.utc)
        results: list[tuple[AggregatedReading, dict | None]] = []
        for rack_key in list(self.window.keys()):
            started_at = self.window_started_at.get(rack_key)
            if started_at is None:
                continue
            if (current_time - started_at).total_seconds() >= batch_interval_seconds:
                aggregate, cloud_payload = self.flush_aggregate(*rack_key)
                if aggregate is not None:
                    results.append((aggregate, cloud_payload))
        return results

    @staticmethod
    def _is_valid(reading: SensorReading) -> bool:
        return (
            reading.value == reading.value
            and reading.value not in {float("inf"), float("-inf")}
            and reading.site.strip() != ""
            and reading.rack_id.strip() != ""
        )

    def flush_all_aggregates(self) -> list[tuple[AggregatedReading, dict | None]]:
        results: list[tuple[AggregatedReading, dict | None]] = []
        for site, rack_id in list(self.window.keys()):
            aggregate, cloud_payload = self.flush_aggregate(site, rack_id)
            if aggregate is not None:
                results.append((aggregate, cloud_payload))
        return results


    @staticmethod
    def _parse_timestamp(value: str) -> datetime:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value).astimezone(timezone.utc)

    def flush_aggregate(self, site: str, rack_id: str) -> tuple[AggregatedReading | None, dict | None]:
        """Flush a rack's readings: returns (simple_aggregate, cloud_payload)."""
        readings = self.window.get((site, rack_id), [])
        if not readings:
            return None, None
        
        # Create cloud-ready payload BEFORE clearing window
        cloud_payload = self._create_cloud_payload(readings, site, rack_id)
        
        # Then create the traditional single-sensor aggregate for compatibility
        latest_by_sensor: dict[SensorType, list[float]] = {}
        units: dict[SensorType, str] = {}
        for reading in readings:
            latest_by_sensor.setdefault(reading.sensor_type, []).append(reading.value)
            units[reading.sensor_type] = reading.unit
        sensor_type = max(latest_by_sensor, key=lambda sensor: len(latest_by_sensor[sensor]))
        values = latest_by_sensor[sensor_type]
        aggregated = AggregatedReading.from_values(
            timestamp=utc_now(),
            site=site,
            rack_id=rack_id,
            sensor_type=sensor_type,
            values=values,
            unit=units[sensor_type],
            window_seconds=len(readings),
        )
        
        # Clear window after we've extracted everything
        self.window[(site, rack_id)] = []
        self.window_started_at.pop((site, rack_id), None)
        return aggregated, cloud_payload

    def _assess_sensor_status(self, sensor_type_str: str, value: float) -> str:
        """Evaluate individual sensor status based on thresholds."""
        t = self.thresholds
        if sensor_type_str == SensorType.TEMPERATURE.value:
            if value >= t.critical_temperature_c:
                return "failed"
            if value >= t.high_temperature_c:
                return "degraded"
        elif sensor_type_str == SensorType.HUMIDITY.value:
            if value >= t.critical_humidity_pct:
                return "failed"
            if value >= t.high_humidity_pct:
                return "degraded"
        elif sensor_type_str == SensorType.POWER.value:
            if value >= t.critical_power_watts:
                return "failed"
            if value >= t.high_power_watts:
                return "degraded"
        elif sensor_type_str == SensorType.UPS.value:
            if value <= t.critical_ups_pct:
                return "failed"
            if value <= t.low_ups_pct:
                return "degraded"
        elif sensor_type_str == SensorType.COOLING.value:
            if value <= t.critical_fan_rpm:
                return "failed"
            if value <= t.low_fan_rpm:
                return "degraded"
        return "healthy"

    def _create_cloud_payload(self, readings: list[SensorReading], site: str, rack_id: str) -> dict:
        """Create a cloud-ready aggregated payload with all 5 sensors."""
        health = self.health_engine.assess(readings)
        sensors_by_type: dict[str, list[float]] = {}
        units: dict[str, str] = {}

        for reading in readings:
            sensor_type_str = reading.sensor_type.value
            sensors_by_type.setdefault(sensor_type_str, []).append(reading.value)
            units[sensor_type_str] = reading.unit

        sensor_summaries = {}
        for sensor_type_str, values in sensors_by_type.items():
            mean_val = sum(values) / len(values) if values else 0.0
            sensor_status = self._assess_sensor_status(sensor_type_str, mean_val)
            sensor_summaries[sensor_type_str] = {
                "value": round(mean_val, 2),
                "unit": units.get(sensor_type_str, ""),
                "count": len(values),
                "status": sensor_status,
            }

        return {
            "site": site,
            "rack_id": rack_id,
            "timestamp": utc_now(),
            "health_score": health.health_score,
            "health_state": health.health_state.value,
            "sensors": sensor_summaries,
        }

