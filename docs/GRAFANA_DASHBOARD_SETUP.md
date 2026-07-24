# EdgeDC360 - Grafana Dashboard & Sensor Failure Setup Guide

This guide explains how to set up and configure Grafana to visualize the aggregated sensor data and monitor sensor failure alerts for EdgeDC360.

---

## 1. Data Source Configuration

1. In Grafana, add a new **Amazon DynamoDB** Data Source (or **AWS CloudWatch** / **Athena** depending on setup).
2. Configure AWS authentication:
   - **Region:** `us-east-1`
   - **Authentication Provider:** AWS SDK Default / IAM Credentials
3. Test the connection.

---

## 2. DynamoDB Table Querying

The DynamoDB table **`EdgeDC360Telemetry`** stores aggregated rack items:
- **Partition Key (`deviceId`):** `site-rack_id` (e.g. `dublin-rack_01`)
- **Sort Key (`timestamp`):** Unix Epoch Timestamp (Number)

### Example Query for Latest Rack Status

To retrieve the latest state for rack `dublin-rack_01`:

```json
{
  "TableName": "EdgeDC360Telemetry",
  "KeyConditionExpression": "deviceId = :id",
  "ExpressionAttributeValues": {
    ":id": { "S": "dublin-rack_01" }
  },
  "ScanIndexForward": false,
  "Limit": 1
}
```

This returns the full item containing all 5 sensors:
```json
{
  "deviceId": "dublin-rack_01",
  "timestamp": 1784719000,
  "site": "dublin",
  "rack_id": "rack_01",
  "health_score": 35,
  "health_state": "critical",
  "status": "CRITICAL",
  "sensors": {
    "temperature": { "value": 88.0, "unit": "C", "status": "failed" },
    "humidity": { "value": 45.0, "unit": "%", "status": "healthy" },
    "power": { "value": 380.0, "unit": "W", "status": "healthy" },
    "ups": { "value": 95.0, "unit": "%", "status": "healthy" },
    "cooling": { "value": 2200.0, "unit": "RPM", "status": "healthy" }
  }
}
```

---

## 3. Configuring Dashboard Panels

### Panel 1: Rack Health Gauge / Status Card
- **Metric:** `health_score`
- **Thresholds:**
  - `80 - 100`: Green (Healthy)
  - `55 - 79`: Yellow (Warning)
  - `0 - 54`: Red (Critical / Failure)

### Panel 2: Sensor Status Matrix (Table / Stat Panel)
Display each sensor's status (`temperature`, `humidity`, `power`, `ups`, `cooling`):
- **Value Mapping:**
  - `"healthy"` → Green
  - `"degraded"` → Orange
  - `"failed"` → Red

---

## 4. End-to-End Failure Testing Workflow

To test manually changing a sensor reading to failure value and verifying Grafana & SNS email alert:

1. **Inject failure via test script:**
   ```powershell
   python .\scripts\test_manual_sensor_failure.py --site dublin --rack rack_01 --sensor temperature --value 88.0 --invoke-lambda
   ```
2. **Verify DynamoDB update:**
   Check `EdgeDC360Telemetry` table in the AWS Console for item `deviceId = "dublin-rack_01"`. The `sensors.temperature.status` field will show `"failed"`.
3. **Verify SNS Email Notification:**
   An email titled `[CRITICAL] Alert for Rack dublin-rack_01` will arrive at your subscribed email address.
4. **Verify Grafana Display:**
   Refresh the Live Operations dashboard panel to see rack status update to `CRITICAL` with temperature highlighted in red.
