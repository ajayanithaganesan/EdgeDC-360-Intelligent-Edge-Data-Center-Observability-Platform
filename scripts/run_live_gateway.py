import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from awscrt import mqtt
from awsiot import mqtt_connection_builder
from config import load_config
from edge_gateway import config as gateway_config
from edge_gateway.processor import EdgeGatewayProcessor
from sensor_simulator.simulator import SensorSimulator


def _normalize_key(key: str) -> str:
    return key.replace("_", "-").replace(" ", "").lower()


def main():
    parser = argparse.ArgumentParser(description="Run the live gateway pipeline with optional anomaly injection")
    parser.add_argument("--fail-sensor", type=str, choices=["temperature", "humidity", "power", "ups", "cooling"], help="Force failure state on a sensor")
    parser.add_argument("--fail-value", type=float, help="Value to inject for the failed sensor")
    parser.add_argument("--fail-rack", type=str, default="Dublin-rack-01", help="Target rack ID to inject failure on (e.g. Dublin-rack-01)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    config = load_config()

    print("==================================================", flush=True)
    print(" EDGE DC360 - LIVE AWS IOT GATEWAY RUNNER", flush=True)
    print("==================================================", flush=True)
    print(f" Connecting to AWS Endpoint: {gateway_config.ENDPOINT}", flush=True)
    print(f" Target Topic:               {gateway_config.TOPIC}", flush=True)
    print(f" Client ID:                   {gateway_config.CLIENT_ID}", flush=True)
    if args.fail_sensor:
        print(f" ANOMALY INJECTION ACTIVE:   {args.fail_rack} -> {args.fail_sensor}={args.fail_value}", flush=True)
    print("==================================================", flush=True)

    # 1. Connect to AWS IoT Core
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
        print("Connecting to AWS IoT Core via mutual TLS...", flush=True)
        connect_future = connection.connect()
        connect_future.result(timeout=15)
        print(">>> SUCCESS: Connected to AWS IoT Core! <<<\n", flush=True)
    except Exception as exc:
        print(f"\n[ERROR] Could not connect to AWS IoT Core: {exc}", flush=True)
        print("Please check your certificates in certificates/ directory and ENDPOINT in edge_gateway/config.py.", flush=True)
        return 1

    # 2. Initialize Simulator & Edge Gateway Processor
    simulator = SensorSimulator(
        sites=config.sensor.sites,
        racks_per_site=config.sensor.racks_per_site,
        seed=config.sensor.seed,
        anomaly_rate=config.sensor.anomaly_rate,
    )
    processor = EdgeGatewayProcessor(config.thresholds)

    # 3. Initialize dynamic metric counters
    metrics_state_file = ROOT / "metrics_state.json"
    state = {
        "racks": {},
        "fog": {
            "generated": 0,
            "filtered": 0,
            "uploaded": 0,
            "bandwidth_saved": 0.0,
            "latency": 5
        },
        "history": {
            "timestamps": [],
            "temperature": [],
            "cooling": [],
            "power": [],
            "ups": []
        }
    }

    batch_interval_seconds = 10
    print(f"Starting continuous telemetry sampling (Batch Aggregation Window = {batch_interval_seconds}s)...", flush=True)
    print("Press Ctrl+C to stop.\n", flush=True)

    try:
        last_flush_time = time.time()
        while True:
            # Sample all sensors across all racks
            readings = simulator.sample_once()
            state["fog"]["generated"] += len(readings)

            # Check for active anomaly signal file (anomaly_active.json)
            anomaly_signal_file = ROOT / "anomaly_active.json"
            active_anomaly = None
            if anomaly_signal_file.exists():
                try:
                    with open(anomaly_signal_file, "r", encoding="utf-8") as af:
                        active_anomaly = json.load(af)
                except Exception:
                    pass

            for reading in readings:
                # Intercept and inject anomaly if target match is met (from CLI args or signal file)
                rack_key = f"{reading.site}-{reading.rack_id}"
                norm_rack_key = _normalize_key(rack_key)
                
                # Check CLI args override
                if args.fail_sensor and norm_rack_key == _normalize_key(args.fail_rack) and reading.sensor_type.value == args.fail_sensor:
                    if args.fail_value is not None:
                        reading.value = args.fail_value
                        reading.anomaly = True
                # Check active anomaly signal file override
                elif active_anomaly and norm_rack_key == _normalize_key(str(active_anomaly.get("rack", ""))) and reading.sensor_type.value == active_anomaly.get("sensor"):
                    reading.value = float(active_anomaly.get("value", 88.0))
                    reading.anomaly = True

                decision = processor.process(reading)

                # If filtered (not critical/alert/forwarded)
                if decision.decision.value == "filtered" or decision.reason == "duplicate reading":
                    state["fog"]["filtered"] += 1
                else:
                    state["fog"]["uploaded"] += 1

            # Check if batch flush window is reached
            now = time.time()
            if now - last_flush_time >= batch_interval_seconds:
                state["fog"]["uploaded"] += len(processor.window) # Count batch flushes
                
                # Calculate bandwidth savings
                total_msgs = state["fog"]["generated"]
                if total_msgs > 0:
                    state["fog"]["bandwidth_saved"] = ((state["fog"]["filtered"]) / total_msgs) * 100.0

                timestamp_str = datetime.now().isoformat()
                
                for site, rack_id in list(processor.window.keys()):
                    cloud_payload = processor.rack_aggregate_for_cloud(site, rack_id)
                    if cloud_payload is not None:
                        # Clear window for this rack
                        processor.window[(site, rack_id)] = []

                        # Publish 5-sensor aggregated item to AWS IoT
                        json_payload = json.dumps(cloud_payload)
                        try:
                            connection.publish(
                                topic=gateway_config.TOPIC,
                                payload=json_payload,
                                qos=mqtt.QoS.AT_LEAST_ONCE,
                            )
                        except Exception as p_err:
                            logging.warning("Local print only; AWS IoT publish skipped: %s", p_err)

                        # Update state representation for local server
                        rack_key = f"{site}-{rack_id}"
                        state["racks"][rack_key] = cloud_payload

                        # Track history using Dublin Rack 01 as target
                        if rack_key == "Dublin-rack-01":
                            state["history"]["timestamps"].append(timestamp_str)
                            state["history"]["temperature"].append(cloud_payload["sensors"]["temperature"]["value"])
                            state["history"]["cooling"].append(cloud_payload["sensors"]["cooling"]["value"])
                            state["history"]["power"].append(cloud_payload["sensors"]["power"]["value"])
                            state["history"]["ups"].append(cloud_payload["sensors"]["ups"]["value"])

                            # Keep history list under 15 items
                            if len(state["history"]["timestamps"]) > 15:
                                for hk in state["history"]:
                                    state["history"][hk].pop(0)

                        health_score = cloud_payload["health_score"]
                        health_state = cloud_payload["health_state"].upper()
                        print(
                            f"[{time.strftime('%H:%M:%S')}] Published to AWS -> {site}-{rack_id} "
                            f"(Health Score: {health_score}/100 [{health_state}], 5 Sensors Aggregated)",
                            flush=True,
                        )

                # Write metrics file for HTTP Server to poll
                try:
                    with open(metrics_state_file, "w", encoding="utf-8") as f:
                        json.dump(state, f)
                except Exception as w_err:
                    logging.warning("Could not write metrics_state.json: %s", w_err)

                last_flush_time = now

            time.sleep(2)

    except KeyboardInterrupt:
        print("\nStopping Gateway...", flush=True)

    print("Disconnecting from AWS IoT Core...", flush=True)
    connection.disconnect()
    print("Done.", flush=True)
    return 0




if __name__ == "__main__":
    raise SystemExit(main())
