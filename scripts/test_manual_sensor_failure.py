"""
Utility script to test manual sensor failure injection and live dashboard alerting.

Usage:
    python scripts/test_manual_sensor_failure.py --site Dublin --rack rack-01 --sensor temperature --value 88.0
    
Press Ctrl+C to stop the failure injection and return the system to normal.
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from edge_gateway.processor import EdgeGatewayProcessor
from config import GatewayThresholds
from shared.models import SensorReading, SensorType


def main():
    parser = argparse.ArgumentParser(description="Inject a continuous sensor failure into the live dashboard and AWS alert engine")
    parser.add_argument("--site", type=str, default="Dublin", help="Site name (e.g. Dublin, Cork, Galway)")
    parser.add_argument("--rack", type=str, default="rack-01", help="Rack ID (e.g. rack-01, rack-02)")
    parser.add_argument("--sensor", type=str, default="temperature", choices=["temperature", "humidity", "power", "ups", "cooling"], help="Sensor to fail")
    parser.add_argument("--value", type=float, default=88.0, help="Failure value to inject")
    parser.add_argument("--invoke-lambda", action="store_true", help="Invoke local lambda_handler function with generated event")

    args = parser.parse_args()

    # Format site and rack_id consistently (e.g. Dublin-rack-01)
    site_formatted = args.site.capitalize()
    rack_formatted = args.rack.replace("_", "-").lower()
    rack_key = f"{site_formatted}-{rack_formatted}"

    processor = EdgeGatewayProcessor(GatewayThresholds())
    now_str = datetime.now(timezone.utc).isoformat()

    # Base nominal values for all 5 sensors
    defaults = {
        SensorType.TEMPERATURE: (22.5, "C"),
        SensorType.HUMIDITY: (45.0, "%"),
        SensorType.POWER: (400.0, "W"),
        SensorType.UPS: (98.0, "%"),
        SensorType.COOLING: (2250.0, "RPM"),
    }

    # Populate processor window with readings
    for stype, (val, unit) in defaults.items():
        if stype.value == args.sensor:
            val = args.value

        reading = SensorReading(
            timestamp=now_str,
            site=site_formatted,
            rack_id=rack_formatted,
            sensor_type=stype,
            value=val,
            unit=unit,
            sequence=1,
            anomaly=(stype.value == args.sensor),
        )
        processor.process(reading)

    cloud_payload = processor.rack_aggregate_for_cloud(site_formatted, rack_formatted)

    print("==================================================")
    print(" EDGE DC360 - MANUAL SENSOR FAILURE INJECTOR")
    print("==================================================")
    print(f" Target Location:            {rack_key}")
    print(f" Target Failed Sensor:       {args.sensor} = {args.value}")
    print(f" Sensor Status:              {cloud_payload['sensors'][args.sensor]['status'].upper()}")
    print(f" Calculated Health Score:    {cloud_payload['health_score']}/100 [{cloud_payload['health_state'].upper()}]")
    print("==================================================")

    if args.invoke_lambda:
        print("\n--- Invoking local lambda_handler ---")
        try:
            from lambda_handler import lambda_handler
            result = lambda_handler(cloud_payload, None)
            print("Lambda Result:", json.dumps(result, indent=2))
        except Exception as l_err:
            print("Lambda invocation error:", l_err)

    signal_file = ROOT / "anomaly_active.json"
    anomaly_payload = {
        "rack": rack_key,
        "sensor": args.sensor,
        "value": args.value
    }

    # Write initial anomaly signal file
    try:
        with open(signal_file, "w", encoding="utf-8") as sf:
            json.dump(anomaly_payload, sf)
    except Exception as s_err:
        print("Signal file error:", s_err)

    print("\n>>> CONTINUOUS FAILURE INJECTION ACTIVE <<<")
    print("The gateway and dashboard will hold this sensor in CRITICAL state without flickering.")
    print("Press Ctrl+C to stop failure injection.\n")

    metrics_file = ROOT / "metrics_state.json"

    try:
        while True:
            # Touch/refresh signal file
            try:
                with open(signal_file, "w", encoding="utf-8") as sf:
                    json.dump(anomaly_payload, sf)
            except Exception:
                pass

            # Also update metrics_state.json directly if gateway is not currently running
            state = {
                "racks": {},
                "fog": {"generated": 100, "filtered": 85, "uploaded": 15, "bandwidth_saved": 85.0, "latency": 5},
                "history": {"timestamps": [], "temperature": [], "cooling": [], "power": [], "ups": []}
            }

            if metrics_file.exists():
                try:
                    with open(metrics_file, "r", encoding="utf-8") as f:
                        state = json.load(f)
                except Exception:
                    pass

            cloud_payload["timestamp"] = datetime.now(timezone.utc).isoformat()
            state["racks"][rack_key] = cloud_payload

            time_str = datetime.now().isoformat()
            state["history"]["timestamps"].append(time_str)
            state["history"]["temperature"].append(cloud_payload["sensors"]["temperature"]["value"])
            state["history"]["cooling"].append(cloud_payload["sensors"]["cooling"]["value"])
            state["history"]["power"].append(cloud_payload["sensors"]["power"]["value"])
            state["history"]["ups"].append(cloud_payload["sensors"]["ups"]["value"])

            if len(state["history"]["timestamps"]) > 15:
                for hk in state["history"]:
                    state["history"][hk].pop(0)

            try:
                with open(metrics_file, "w", encoding="utf-8") as f:
                    json.dump(state, f)
            except Exception:
                pass

            print(f"[{time.strftime('%H:%M:%S')}] Active Anomaly -> {rack_key} ({args.sensor}={args.value} [{cloud_payload['health_state'].upper()}])", flush=True)
            time.sleep(2)

    except KeyboardInterrupt:
        print("\nStopping failure injection script...", flush=True)
    finally:
        if signal_file.exists():
            try:
                signal_file.unlink()
            except Exception:
                pass
        print("System telemetry returning to healthy baseline.", flush=True)

if __name__ == "__main__":
    main()
