"""CLI entrypoint for the edge gateway processor."""

from __future__ import annotations

import argparse
import json
import logging
import socket
import sys
import threading
import time
import uuid
from pathlib import Path

from awscrt import mqtt as awscrt_mqtt
from awsiot import mqtt_connection_builder

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import load_config
from edge_gateway import config as gateway_config
from edge_gateway.processor import EdgeGatewayProcessor
from edge_gateway.storage import SQLiteOfflineBuffer
from shared.models import reading_from_payload, sensor_wildcard
from shared.mqtt_client import MQTTClient, MQTTUnavailableError



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Process EdgeDC360 telemetry from JSON lines")
    parser.add_argument("--input", type=str, default="-", help="JSONL input file or - for stdin")
    parser.add_argument("--buffer-offline", action="store_true", help="Store outputs in SQLite instead of printing")
    parser.add_argument("--mqtt", action="store_true", help="Subscribe to MQTT instead of reading stdin")
    parser.add_argument("--batch", action="store_true", help="Emit aggregated windows instead of per-reading decisions")
    parser.add_argument("--batch-interval-seconds", type=int, default=30, help="Time window in seconds for producing each aggregate")
    return parser


def _iter_lines(path: str):
    if path == "-":
        yield from sys.stdin
        return
    with open(path, "r", encoding="utf-8") as handle:
        yield from handle


def _should_publish_to_cloud(decision_type: str | None) -> bool:
    if decision_type is None:
        return False
    return decision_type.lower() == "filtered"


AWS_CONNECTION = None
RACK_AGGREGATES = {}  # Track which racks have been published for each batch window


def _get_aws_connection() -> object | None:
    global AWS_CONNECTION
    if AWS_CONNECTION is not None:
        return AWS_CONNECTION

    try:
        connection = mqtt_connection_builder.mtls_from_path(
            endpoint=gateway_config.ENDPOINT,
            cert_filepath=gateway_config.CERTIFICATE,
            pri_key_filepath=gateway_config.PRIVATE_KEY,
            client_bootstrap=None,
            ca_filepath=gateway_config.ROOT_CA,
            client_id=gateway_config.CLIENT_ID,
            clean_session=False,
            keep_alive_secs=30,
        )
        connect_future = connection.connect()
        connect_future.result(timeout=10)
        AWS_CONNECTION = connection
        return connection
    except Exception as exc:  # pragma: no cover - defensive logging for local environments
        logging.warning("AWS IoT connection unavailable; continuing with local output only: %s", exc)
        return None


def _emit_output(args, buffer, processor, *, decision=None, aggregate=None, cloud_payload=None) -> None:
    if aggregate is not None:
        payload = aggregate.to_dict()
        if args.buffer_offline:
            buffer.enqueue(created_at=aggregate.timestamp, topic="edge/aggregate", payload=payload)
        else:
            # In batch mode, print debug info instead of full payload
            if args.batch:
                health_score = cloud_payload.get("health_score", "N/A") if cloud_payload else "N/A"
                print(f"[BATCH_AGGREGATE] {aggregate.site}-{aggregate.rack_id} at {aggregate.timestamp}: health_score={health_score}", flush=True)
            else:
                print(json.dumps(payload, separators=(",", ":")), flush=True)


        if args.batch and cloud_payload is not None:
            # Publish rack-level aggregate to AWS (combines all 5 sensors)
            aws_connection = _get_aws_connection()
            if aws_connection is not None:
                try:
                    aws_connection.publish(
                        topic=gateway_config.TOPIC,
                        payload=json.dumps(cloud_payload),
                        qos=awscrt_mqtt.QoS.AT_LEAST_ONCE,
                    )
                    logging.info(
                        "Published aggregated rack data to AWS IoT topic %s: %s-%s",
                        gateway_config.TOPIC,
                        cloud_payload.get("site"),
                        cloud_payload.get("rack_id"),
                    )
                except Exception as exc:  # pragma: no cover
                    logging.warning("Failed to publish rack aggregate to AWS IoT: %s", exc)
    elif decision is not None:
        payload = decision.to_dict()
        if args.buffer_offline:
            buffer.enqueue(created_at=decision.timestamp, topic="edge/decision", payload=payload)
        else:
            if not args.batch:
                # Only print individual decisions in non-batch mode
                print(json.dumps(payload, separators=(",", ":")))

        # Only publish individual decisions to AWS in non-batch mode
        if not args.batch and _should_publish_to_cloud(payload.get("decision")):
            aws_connection = _get_aws_connection()
            if aws_connection is not None:
                try:
                    aws_connection.publish(
                        topic=gateway_config.TOPIC,
                        payload=json.dumps(payload),
                        qos=awscrt_mqtt.QoS.AT_LEAST_ONCE,
                    )
                    logging.info("Published decision to AWS IoT topic %s", gateway_config.TOPIC)
                except Exception as exc:  # pragma: no cover - defensive logging for local environments
                    logging.warning("Failed to publish decision to AWS IoT: %s", exc)


def main() -> int:
    config = load_config()
    logging.basicConfig(level=config.log_level.upper(), format="%(asctime)s %(levelname)s %(message)s")
    args = build_parser().parse_args()

    processor = EdgeGatewayProcessor(config.thresholds)
    buffer = SQLiteOfflineBuffer(config.storage.sqlite_path)

    if args.mqtt:
        try:
            mqtt_client = MQTTClient.create(f"{config.mqtt.client_id_prefix}-gateway-{uuid.uuid4().hex[:8]}")
            mqtt_client.set_credentials(config.mqtt.username, config.mqtt.password)
            mqtt_client.connect(config.mqtt.host, config.mqtt.port, config.mqtt.keepalive)
            mqtt_client.subscribe(sensor_wildcard(config.mqtt.sensor_topic_prefix))

            def handle_message(_client, _userdata, message) -> None:
                payload = json.loads(message.payload.decode("utf-8"))
                reading = reading_from_payload(payload)
                if args.batch:
                    decision, aggregate, cloud_payload = processor.process_and_flush(reading, batch_interval_seconds=args.batch_interval_seconds)
                    _emit_output(args, buffer, processor, decision=decision, aggregate=aggregate, cloud_payload=cloud_payload)
                else:
                    decision = processor.process(reading)
                    _emit_output(args, buffer, processor, decision=decision)

            mqtt_client.on_message(handle_message)
            mqtt_client.loop_forever()
            return 0
        except (ConnectionRefusedError, OSError, socket.gaierror) as exc:
            logging.error(
                "MQTT broker is not reachable at %s:%s. Start a broker first, or use "
                "`python .\\scripts\\run_local_smoke_test.py` to test without MQTT. Details: %s",
                config.mqtt.host,
                config.mqtt.port,
                exc,
            )
            return 1
        except MQTTUnavailableError as exc:
            logging.error(str(exc))
            return 1

    if args.batch:
        stop_event = threading.Event()

        def periodic_flush() -> None:
            while not stop_event.is_set():
                time.sleep(1)
                for aggregate, cloud_payload in processor.flush_due_aggregates(batch_interval_seconds=args.batch_interval_seconds):
                    _emit_output(args, buffer, processor, aggregate=aggregate, cloud_payload=cloud_payload)

        flush_thread = threading.Thread(target=periodic_flush, daemon=True)
        flush_thread.start()

    try:
        for raw_line in _iter_lines(args.input):
            line = raw_line.strip()
            if not line:
                continue
            payload = json.loads(line)
            reading = reading_from_payload(payload)
            if args.batch:
                decision, aggregate, cloud_payload = processor.process_and_flush(reading, batch_interval_seconds=args.batch_interval_seconds)
                _emit_output(args, buffer, processor, decision=decision, aggregate=aggregate, cloud_payload=cloud_payload)
            else:
                decision = processor.process(reading)
                _emit_output(args, buffer, processor, decision=decision)
    finally:
        if args.batch:
            stop_event.set()
            flush_thread.join(timeout=1)

    if args.batch:
        for aggregate, cloud_payload in processor.flush_all_aggregates():
            _emit_output(args, buffer, processor, aggregate=aggregate, cloud_payload=cloud_payload)

    return 0



if __name__ == "__main__":
    raise SystemExit(main())
