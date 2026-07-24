"""No-Docker local smoke test for EdgeDC360."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import load_config
from edge_gateway.processor import EdgeGatewayProcessor
from edge_gateway.storage import SQLiteOfflineBuffer
from sensor_simulator.simulator import SensorSimulator
from shared.models import reading_from_payload



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a local EdgeDC360 smoke test without Docker")
    parser.add_argument("--cycles", type=int, default=1, help="Number of sampling cycles to run")
    parser.add_argument("--buffer-offline", action="store_true", help="Store gateway outputs in SQLite")
    return parser


def main() -> int:
    config = load_config()
    args = build_parser().parse_args()

    simulator = SensorSimulator(
        sites=config.sensor.sites,
        racks_per_site=config.sensor.racks_per_site,
        seed=config.sensor.seed,
        anomaly_rate=config.sensor.anomaly_rate,
    )
    processor = EdgeGatewayProcessor(config.thresholds)
    buffer = SQLiteOfflineBuffer(config.storage.sqlite_path)

    for _ in range(args.cycles):
        for reading in simulator.sample_once():
            payload = reading.to_dict()
            restored = reading_from_payload(payload)
            decision = processor.process(restored)
            if args.buffer_offline:
                buffer.enqueue(created_at=decision.timestamp, topic="edge/decision", payload=decision.to_dict())
            else:
                print(json.dumps(decision.to_dict(), separators=(",", ":")))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
