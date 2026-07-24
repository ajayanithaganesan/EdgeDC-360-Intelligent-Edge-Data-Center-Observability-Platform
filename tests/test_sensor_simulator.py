import unittest

import importlib
from unittest.mock import Mock

from sensor_simulator.temperature_sensor import TemperatureSensor
from sensor_simulator.humidity_sensor import HumiditySensor
from sensor_simulator.power_sensor import PowerSensor
from sensor_simulator.ups_sensor import UPSBatterySensor
from sensor_simulator.cooling_sensor import CoolingSensor
from shared.models import DecisionType, SensorType, SensorReading
from config import GatewayThresholds
from edge_gateway import config as gateway_config
from edge_gateway.processor import EdgeGatewayProcessor
from edge_gateway.main import _should_publish_to_cloud


class SensorModuleTests(unittest.TestCase):
    def test_sensor_modules_generate_realistic_values(self) -> None:
        sensors = [
            TemperatureSensor(),
            HumiditySensor(),
            PowerSensor(),
            UPSBatterySensor(),
            CoolingSensor(),
        ]

        expected_types = {
            SensorType.TEMPERATURE,
            SensorType.HUMIDITY,
            SensorType.POWER,
            SensorType.UPS,
            SensorType.COOLING,
        }
        self.assertEqual({sensor.sensor_type for sensor in sensors}, expected_types)

        for sensor in sensors:
            value, anomaly = sensor.generate(None, 20.0, 0.0)
            self.assertIsInstance(value, float)
            self.assertIsInstance(anomaly, bool)

    def test_cli_entrypoints_import_cleanly(self) -> None:
        importlib.import_module("sensor_simulator.main")
        importlib.import_module("edge_gateway.main")

    def test_should_publish_to_cloud_filters_for_filtered_decisions(self) -> None:
        self.assertTrue(_should_publish_to_cloud("filtered"))
        self.assertFalse(_should_publish_to_cloud("forwarded"))
        self.assertFalse(_should_publish_to_cloud("within nominal range"))

    def test_gateway_config_resolves_certificate_paths(self) -> None:
        for path_value in (gateway_config.ROOT_CA, gateway_config.CERTIFICATE, gateway_config.PRIVATE_KEY):
            self.assertTrue(path_value.startswith(("/", "C:/", "C:\\")))
            self.assertTrue(path_value.endswith((".pem", ".crt", ".key")))

    def test_invalid_reading_is_filtered(self) -> None:
        processor = EdgeGatewayProcessor(GatewayThresholds())
        reading = SensorReading(
            timestamp="2026-01-01T00:00:00Z",
            site="Dublin",
            rack_id="rack-01",
            sensor_type=SensorType.TEMPERATURE,
            value=float("nan"),
            unit="C",
            sequence=1,
        )

        decision = processor.process(reading)
        self.assertEqual(decision.decision, DecisionType.FILTERED)
        self.assertEqual(decision.reason, "invalid reading")
        self.assertFalse(decision.upload)
