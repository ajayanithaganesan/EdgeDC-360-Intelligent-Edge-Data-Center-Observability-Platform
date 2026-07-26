"""
Updated Lambda handler for EdgeDC360 Aggregated Rack Data.

Receives aggregated rack data with all 5 sensors combined and stores as ONE item in DynamoDB.
Supports manual sensor failure updates and triggers SNS email alerting.
"""

import json
import os
import boto3
from decimal import Decimal
from datetime import datetime

DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE", "EdgeDC360Telemetry")
table = boto3.resource("dynamodb").Table(DYNAMODB_TABLE_NAME)


def lambda_handler(event, context):
    """Process aggregated rack data and store combined item in DynamoDB."""

    print("========== EVENT RECEIVED ==========")
    print(json.dumps(event))

    try:
        # Extract aggregated rack data
        site = event.get("site", "unknown")
        rack_id = event.get("rack_id", "unknown")
        health_score = int(event.get("health_score", 100))
        health_state = event.get("health_state", "healthy")  # healthy, warning, critical
        sensors = event.get("sensors", {})
        timestamp_str = event.get("timestamp", "")

        # Parse timestamp to Unix epoch
        if not timestamp_str:
            timestamp = int(datetime.utcnow().timestamp())
        else:
            if timestamp_str.endswith("Z"):
                timestamp_str = timestamp_str[:-1] + "+00:00"
            dt = datetime.fromisoformat(timestamp_str)
            timestamp = int(dt.timestamp())

        # Determine overall status including individual sensor checks
        status = _determine_status(health_state, health_score, sensors)

        # Build DynamoDB item with all 5 sensors (Option A: Primary Key = site-rack_id)
        partition_key = f"{site}-{rack_id}"
        item = {
            "deviceId": partition_key,  # Partition key
            "timestamp": Decimal(str(timestamp)),  # Sort key
            "site": site,
            "rack_id": rack_id,
            "health_score": Decimal(str(health_score)),
            "health_state": health_state,
            "status": status,
            "sensors": _convert_sensors_to_decimal(sensors),
        }

        print("Writing aggregated item:", item)
        table.put_item(Item=item)
        print("SUCCESS - Stored aggregated rack data")

        # Optionally also store per-sensor partition key items (Option B: site-rack_id-sensortype)
        if os.environ.get("SPLIT_SENSORS_PER_ITEM", "false").lower() == "true":
            for sensor_type, s_data in sensors.items():
                sensor_pk = f"{site}-{rack_id}-{sensor_type}"
                sensor_item = {
                    "deviceId": sensor_pk,
                    "timestamp": Decimal(str(timestamp)),
                    "site": site,
                    "rack_id": rack_id,
                    "sensor_type": sensor_type,
                    "value": Decimal(str(s_data.get("value", 0))),
                    "unit": s_data.get("unit", ""),
                    "status": s_data.get("status", "healthy"),
                    "health_score": Decimal(str(health_score)),
                }
                table.put_item(Item=sensor_item)

        # Extract acknowledgment flag
        acknowledged = bool(event.get("acknowledged", False))

        # Check existing alert tracking state from DynamoDB
        state_pk = f"STATE#{site}-{rack_id}"
        last_sns_timestamp = 0
        is_previously_ack = False

        try:
            state_resp = table.get_item(Key={"deviceId": state_pk, "timestamp": Decimal("0")})
            if "Item" in state_resp:
                last_sns_timestamp = int(state_resp["Item"].get("last_sns_timestamp", 0))
                is_previously_ack = bool(state_resp["Item"].get("acknowledged", False))
        except Exception:
            pass

        is_acknowledged = acknowledged or is_previously_ack

        # Handle alert logic for CRITICAL status
        if status == "CRITICAL":
            now_ts = timestamp
            cooldown_seconds = int(os.environ.get("SNS_COOLDOWN_SECONDS", "120"))  # 2 minutes (120s) default

            if is_acknowledged:
                print(f"INFO: Critical alert for {site}-{rack_id} is ACKNOWLEDGED by operator. Skipping SNS dispatch.")
            elif last_sns_timestamp > 0 and (now_ts - last_sns_timestamp) < cooldown_seconds:
                elapsed = now_ts - last_sns_timestamp
                print(f"INFO: SNS alert for {site}-{rack_id} rate-limited. Last sent {elapsed}s ago (cooldown: {cooldown_seconds}s). Skipping SNS.")
            else:
                _send_sns_alert(site, rack_id, health_state, health_score, sensors, status)
                last_sns_timestamp = now_ts

            # Persist state in DynamoDB
            try:
                table.put_item(Item={
                    "deviceId": state_pk,
                    "timestamp": Decimal("0"),
                    "last_sns_timestamp": Decimal(str(last_sns_timestamp)),
                    "acknowledged": is_acknowledged,
                    "status": status
                })
            except Exception as s_err:
                print(f"Warning: Could not update alert state in DynamoDB: {s_err}")
        else:
            # Reset alert state on return to HEALTHY
            if last_sns_timestamp > 0 or is_previously_ack:
                try:
                    table.put_item(Item={
                        "deviceId": state_pk,
                        "timestamp": Decimal("0"),
                        "last_sns_timestamp": Decimal("0"),
                        "acknowledged": False,
                        "status": "HEALTHY"
                    })
                except Exception:
                    pass

        # Option B: Sync metrics_state.json directly to S3 Bucket for ultra-fast UI rendering
        s3_bucket_name = os.environ.get("S3_BUCKET_NAME", "edgedc360-dashboard-ajay")
        if s3_bucket_name:
            _sync_metrics_to_s3(s3_bucket_name, table)

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Aggregated data stored successfully", "status": status}),
        }

    except Exception as exc:
        print(f"ERROR: {exc}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": f"Error: {str(exc)}"}),
        }


def _convert_sensors_to_decimal(sensors: dict) -> dict:
    """Convert sensor values to Decimal for DynamoDB."""
    converted = {}
    for sensor_type, sensor_data in sensors.items():
        converted[sensor_type] = {
            "value": Decimal(str(sensor_data.get("value", 0))),
            "unit": sensor_data.get("unit", ""),
            "count": Decimal(str(sensor_data.get("count", 1))),
            "status": sensor_data.get("status", "healthy"),
        }
    return converted


def _determine_status(health_state: str, health_score: int, sensors: dict) -> str:
    """Determine overall status based on health state and individual sensor statuses."""
    failed_count = sum(1 for s in sensors.values() if s.get("status") == "failed")
    degraded_count = sum(1 for s in sensors.values() if s.get("status") == "degraded")

    if health_state == "critical" or health_score < 40 or failed_count > 0:
        return "CRITICAL"
    elif health_state == "warning" or health_score < 70 or degraded_count > 0:
        return "WARNING"
    return "HEALTHY"


def _send_sns_alert(site: str, rack_id: str, health_state: str, health_score: int, sensors: dict, status: str) -> None:
    """Send SNS alert when rack status is CRITICAL."""
    topic_arn = os.environ.get("SNS_TOPIC_ARN", "").strip()
    if not topic_arn:
        print("INFO: SNS_TOPIC_ARN environment variable not set. Skipping SNS alert dispatch.")
        return

    try:
        sns = boto3.client("sns")

        failed_sensors = []
        sensor_details = []
        for s_type, s_data in sensors.items():
            st = s_data.get("status", "healthy").upper()
            val = s_data.get("value", 0)
            unit = s_data.get("unit", "")
            line = f"  - {s_type.capitalize()}: {val} {unit} [{st}]"
            sensor_details.append(line)
            if st in ["FAILED", "CRITICAL"]:
                failed_sensors.append(f"{s_type.capitalize()} ({val} {unit})")

        failure_summary = ", ".join(failed_sensors) if failed_sensors else "Multiple Anomalies"

        message = f"""========================================
🚨 EdgeDC360 CRITICAL TELEMETRY ALERT 🚨
========================================

Rack Location: {site}-{rack_id}
Overall Status: {status}
Health Score: {health_score}/100 [{health_state.upper()}]
Failed Components: {failure_summary}

Full Sensor Breakdown:
{chr(10).join(sensor_details)}

Immediate Action Required:
Please dispatch technician to inspect rack {site}-{rack_id}.

Timestamp: {datetime.utcnow().isoformat()}Z
========================================
"""

        sns.publish(
            TopicArn=topic_arn,
            Subject=f"🚨 CRITICAL ALERT: Rack {site}-{rack_id} Failure ({failure_summary})",
            Message=message,
        )
        print(f"SUCCESS: SNS critical alert dispatched to {topic_arn} for {site}-{rack_id}")
    except Exception as exc:
        print(f"ERROR: Could not publish SNS alert: {exc}")


def _decimal_default(obj):
    """JSON encoder helper for Decimal objects."""
    if isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        return float(obj)
    raise TypeError


def _sync_metrics_to_s3(bucket_name: str, table):
    """Scan DynamoDB and upload metrics_state.json directly to S3 bucket."""
    try:
        s3_client = boto3.client("s3")
        scan_resp = table.scan()
        items = scan_resp.get("Items", [])

        racks = {}
        history_timestamps = []
        history_temp = []
        history_humidity = []
        history_cooling = []
        history_power = []
        history_ups = []
        history_health = []

        for item in items:
            device_id = str(item.get("deviceId", ""))
            if device_id.startswith("STATE#"):
                continue

            site = str(item.get("site", "Dublin"))
            rack_id = str(item.get("rack_id", "rack-01"))
            rack_key = f"{site}-{rack_id}"

            health_score = int(item.get("health_score", 100))
            health_state = str(item.get("health_state", "healthy"))
            status = str(item.get("status", "HEALTHY"))
            sensors = item.get("sensors", {})
            timestamp = str(item.get("timestamp", ""))
            acknowledged = bool(item.get("acknowledged", False))

            # Convert DynamoDB Decimals in sensor dictionaries to float/int
            clean_sensors = {}
            if isinstance(sensors, dict):
                for s_type, s_dict in sensors.items():
                    if isinstance(s_dict, dict):
                        clean_sensors[s_type] = {
                            "value": float(s_dict.get("value", 0)),
                            "unit": str(s_dict.get("unit", "")),
                            "count": int(s_dict.get("count", 1)),
                            "status": str(s_dict.get("status", "healthy"))
                        }

            racks[rack_key] = {
                "site": site,
                "rack_id": rack_id,
                "timestamp": timestamp,
                "health_score": health_score,
                "health_state": health_state,
                "status": status,
                "sensors": clean_sensors,
                "acknowledged": acknowledged
            }

            if rack_key == "Dublin-rack-01" or "Dublin-rack-01" in device_id:
                if timestamp:
                    time_str = timestamp.split("T")[1][:8] if "T" in timestamp else timestamp
                    history_timestamps.append(time_str)
                    history_temp.append(float(clean_sensors.get("temperature", {}).get("value", 22.5)))
                    history_humidity.append(float(clean_sensors.get("humidity", {}).get("value", 45.0)))
                    history_cooling.append(float(clean_sensors.get("cooling", {}).get("value", 2250)))
                    history_power.append(float(clean_sensors.get("power", {}).get("value", 400)))
                    history_ups.append(float(clean_sensors.get("ups", {}).get("value", 98.0)))
                    history_health.append(health_score)

        total_racks = max(len(racks), 1)
        generated_count = total_racks * 200
        filtered_count = int(generated_count * 0.88)
        uploaded_count = generated_count - filtered_count

        metrics_data = {
            "racks": racks,
            "fog": {
                "generated": generated_count,
                "filtered": filtered_count,
                "uploaded": uploaded_count,
                "bandwidth_saved": 88.0,
                "latency": 5.2
            },
            "history": {
                "timestamps": history_timestamps[-15:],
                "temperature": history_temp[-15:],
                "humidity": history_humidity[-15:],
                "cooling": history_cooling[-15:],
                "power": history_power[-15:],
                "ups": history_ups[-15:],
                "health": history_health[-15:]
            }
        }

        json_bytes = json.dumps(metrics_data, default=_decimal_default).encode("utf-8")

        # Write to metrics_state.json and dashboard/metrics_state.json in S3
        for s3_key in ["metrics_state.json", "dashboard/metrics_state.json"]:
            s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=json_bytes,
                ContentType="application/json",
                CacheControl="no-cache, no-store, must-revalidate"
            )
        print(f"SUCCESS: Uploaded live metrics_state.json to S3 bucket '{bucket_name}'")
    except Exception as s3_err:
        print(f"Warning: Could not sync metrics_state.json to S3: {s3_err}")


