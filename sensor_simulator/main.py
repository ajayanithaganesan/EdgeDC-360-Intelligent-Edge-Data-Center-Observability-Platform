"""CLI entrypoint for the sensor simulator."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import load_config
from sensor_simulator.simulator import SensorSimulator
from shared.models import sensor_topic
from shared.mqtt_client import MQTTClient, MQTTUnavailableError



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate EdgeDC360 telemetry")
    parser.add_argument("--cycles", type=int, default=1, help="Number of sampling cycles to emit (0 for continuous infinite mode)")
    parser.add_argument("--continuous", action="store_true", help="Run indefinitely until stopped")
    parser.add_argument("--sleep", type=float, default=2.0, help="Pause between cycles in seconds")
    parser.add_argument("--jsonl", action="store_true", help="Emit JSON Lines instead of human-readable text")
    parser.add_argument("--mqtt", action="store_true", help="Publish readings to MQTT instead of printing")
    return parser


def main() -> int:
    config = load_config()
    logging.basicConfig(level=config.log_level.upper(), format="%(asctime)s %(levelname)s %(message)s")
    args = build_parser().parse_args()

    simulator = SensorSimulator(
        sites=config.sensor.sites,
        racks_per_site=config.sensor.racks_per_site,
        seed=config.sensor.seed,
        anomaly_rate=config.sensor.anomaly_rate,
    )

    mqtt_client = None
    if args.mqtt:
        if not config.mqtt.enabled:
            logging.warning("MQTT mode requested but EDGEDC360_MQTT_ENABLED is false; attempting to connect anyway")
        try:
            mqtt_client = MQTTClient.create(f"{config.mqtt.client_id_prefix}-sensor-{uuid.uuid4().hex[:8]}")
            mqtt_client.set_credentials(config.mqtt.username, config.mqtt.password)
            mqtt_client.connect(config.mqtt.host, config.mqtt.port, config.mqtt.keepalive)
            mqtt_client.loop_start()
            logging.info("Connected to MQTT broker at %s:%s", config.mqtt.host, config.mqtt.port)
        except MQTTUnavailableError as exc:
            logging.error(str(exc))
            return 1

    infinite_mode = args.continuous or args.cycles <= 0
    cycle = 0

    try:
        while infinite_mode or cycle < args.cycles:
            readings = simulator.sample_once()
            for reading in readings:
                if mqtt_client is not None:
                    topic = sensor_topic(config.mqtt.sensor_topic_prefix, reading)
                    mqtt_client.publish(topic, reading.to_json())
                elif args.jsonl:
                    print(json.dumps(reading.to_dict(), separators=(",", ":")))
                else:
                    print(f"{reading.timestamp} {reading.site} {reading.rack_id} {reading.sensor_type.value}={reading.value}{reading.unit}")
            
            cycle += 1
            if (infinite_mode or cycle < args.cycles) and args.sleep > 0:
                time.sleep(args.sleep)
    except KeyboardInterrupt:
        logging.info("Stopping sensor simulator...")

    if mqtt_client is not None:
        mqtt_client.loop_stop()

    return 0



if __name__ == "__main__":
    raise SystemExit(main())
