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

        # Trigger SNS alert if status is WARNING or CRITICAL
        if status in ["WARNING", "CRITICAL"]:
            _send_sns_alert(site, rack_id, health_state, health_score, sensors, status)

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
    """Send SNS alert when rack status is WARNING or CRITICAL."""
    try:
        sns = boto3.client("sns")
        topic_arn = os.environ.get("SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:EdgeDC360Alerts")

        sensor_details = []
        for s_type, s_data in sensors.items():
            st = s_data.get("status", "healthy").upper()
            val = s_data.get("value", 0)
            unit = s_data.get("unit", "")
            sensor_details.append(f"  - {s_type.capitalize()}: {val} {unit} [{st}]")

        message = f"""========================================
EdgeDC360 RACK TELEMETRY ALERT
========================================

Site: {site}
Rack ID: {rack_id}
Overall Status: {status}
Health Score: {health_score}/100 ({health_state.upper()})

Sensor Readings Breakdown:
{chr(10).join(sensor_details)}

Action Required: Please inspect rack {site}-{rack_id} immediately.
========================================
"""

        sns.publish(
            TopicArn=topic_arn,
            Subject=f"[{status}] Alert for Rack {site}-{rack_id}",
            Message=message,
        )
        print(f"SNS alert sent for {site}-{rack_id}")
    except Exception as exc:
        print(f"Warning: Could not send SNS alert: {exc}")

