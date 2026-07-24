import unittest

from config import GatewayThresholds
from edge_gateway.processor import EdgeGatewayProcessor
from shared.models import SensorReading, SensorType


class EdgeGatewayProcessorBatchTests(unittest.TestCase):
    def test_flush_aggregate_returns_summary_for_time_window(self) -> None:
        processor = EdgeGatewayProcessor(GatewayThresholds())

        first_reading = SensorReading(
            timestamp="2026-01-01T00:00:00Z",
            site="Dublin",
            rack_id="rack-01",
            sensor_type=SensorType.TEMPERATURE,
            value=21.0,
            unit="C",
            sequence=1,
        )
        second_reading = SensorReading(
            timestamp="2026-01-01T00:00:30Z",
            site="Dublin",
            rack_id="rack-01",
            sensor_type=SensorType.TEMPERATURE,
            value=23.0,
            unit="C",
            sequence=2,
        )

        first_decision, first_aggregate, _ = processor.process_and_flush(first_reading, batch_interval_seconds=30)
        self.assertIsNotNone(first_decision)
        self.assertIsNone(first_aggregate)

        second_decision, second_aggregate, cloud_payload = processor.process_and_flush(second_reading, batch_interval_seconds=30)
        self.assertIsNotNone(second_decision)
        self.assertIsNotNone(second_aggregate)
        self.assertIsNotNone(cloud_payload)
        self.assertEqual(second_aggregate.count, 2)
        self.assertEqual(second_aggregate.minimum, 21.0)
        self.assertEqual(second_aggregate.maximum, 23.0)
        self.assertAlmostEqual(second_aggregate.mean, 22.0)
        self.assertAlmostEqual(second_aggregate.standard_deviation, 1.0)



if __name__ == "__main__":
    unittest.main()
