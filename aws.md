# EdgeDC360 - AWS Backend & Cloud Architecture Specification

> This document summarizes all AWS resources, configurations, architecture flows, and integration policies that have been created and configured in the AWS Console and local workspace repository.

---

# 🌐 Overall Cloud Architecture & Pipeline

The system implements a streamlined **Fog/Edge + AWS Cloud Architecture** using a single high-performance Lambda ingestion engine and S3 direct JSON sync:

```text
               ┌──────────────────────────────────────────────┐
               │ ⚡ LOCAL FOG & SENSOR LAYER                  │
               │ • 5-Sensor Physical Simulators                │
               │ • Sliding Window Fog Processor & Deduplicator │
               │ • CLI Dispatch Frequency & Anomaly Injector   │
               └──────────────────────┬───────────────────────┘
                                      │
           ┌──────────────────────────┴──────────────────────────┐
           │                                                     │
           ▼ (Sub-second local sync)                             ▼ (Configurable Batch Window: ~10s)
 ┌───────────────────────────┐                         ┌──────────────────────────────────┐
 │  LOCAL OPERATIONS PATH    │                         │   AWS PUBLIC CLOUD BACKEND       │
 │                           │                         │                                  │
 │ • Write metrics_state.json│                         │ • AWS IoT Core (Mutual TLS)      │
 │ • Localhost Web Server    │                         │ • AWS IoT Rule                   │
 │                           │                         │ • Single Ingest Lambda Handler   │
 └───────────────────────────┘                         │   (lambda_handler.py)            │
                                                       │   ├──► AWS DynamoDB              │
                                                       │   ├──► AWS SNS (Email Alerts)    │
                                                       │   └──► AWS S3 (Live JSON Sync)   │
                                                       └────────────────┬─────────────────┘
                                                                        │
                                                                        ▼ (HTTP ~15ms Direct S3 Fetch)
                                                       ┌──────────────────────────────────┐
                                                       │  AWS S3 STATIC WEBSITE DASHBOARD │
                                                       │  (edgedc360-dashboard-ajay)      │
                                                       └──────────────────────────────────┘
```

---

# 📍 AWS Deployment Region

```text
us-east-1 (N. Virginia)
```

---

# 1. AWS IoT Core Ingestion Layer

## IoT Thing
- **Thing Name**: `EdgeDC360Gateway`

## Authentication & Security
Mutual TLS authentication using X.509 certificates:
- **Device Certificate**: `device.pem.crt`
- **Private Key**: `private.pem.key`
- **Amazon Root CA**: `AmazonRootCA1.pem`

## IoT Policy (`EdgeDC360Policy`)
Permissions granted:
- `iot:Connect` (Client ID: `EdgeDC360Gateway`)
- `iot:Publish` (Topic: `edgedc360/telemetry`)
- `iot:Subscribe`
- `iot:Receive`

## MQTT Telemetry Schema
- **Target Topic**: `edgedc360/telemetry`
- **Dispatch Frequency**: Configurable via CLI (`--batch-interval`, default `10.0` seconds)

### Aggregated Payload Structure (5 Sensors + Health Score)
```json
{
    "site": "Dublin",
    "rack_id": "rack-01",
    "timestamp": "2026-07-26T02:15:42.123456+00:00",
    "health_score": 99,
    "health_state": "healthy",
    "status": "HEALTHY",
    "acknowledged": false,
    "sensors": {
        "temperature": {"value": 22.58, "unit": "C", "count": 5, "status": "healthy"},
        "humidity": {"value": 44.92, "unit": "%", "count": 5, "status": "healthy"},
        "power": {"value": 400.95, "unit": "W", "count": 5, "status": "healthy"},
        "ups": {"value": 98.05, "unit": "%", "count": 5, "status": "healthy"},
        "cooling": {"value": 2258.69, "unit": "RPM", "count": 5, "status": "healthy"}
    }
}
```

---

# 2. AWS IoT Rule Routing

- **Rule Name**: `EdgeDC360TelemetryRule`
- **SQL Statement**: `SELECT * FROM 'edgedc360/telemetry'`
- **SQL Version**: `2016-03-23`
- **Target Action**: Invoke AWS Lambda Function (`lambda_handler`)

---

# 3. AWS Lambda Function (Single Core Engine)

- **Function Name**: `lambda_handler` (or `EdgeDC360TelemetryProcessor`)
- **Runtime**: `Python 3.12`
- **Timeout**: `15 seconds`
- **Environment Variables**:
  - `DYNAMODB_TABLE`: `EdgeDC360Telemetry`
  - `SNS_TOPIC_ARN`: `arn:aws:sns:us-east-1:...:EdgeDC360CriticalAlerts`
  - `SNS_COOLDOWN_SECONDS`: `120`
  - `S3_BUCKET_NAME`: `edgedc360-dashboard-ajay`
- **Core Operations**:
  1. Receives MQTT telemetry payload from **AWS IoT Core**.
  2. Stores aggregated 5-sensor payload into **AWS DynamoDB**.
  3. Enforces 2-minute (120s) rate-limiting cooldown and operator acknowledgment checks.
  4. Triggers **AWS SNS** critical email/SMS alerts on failure injection (e.g. Temperature = 88.0°C).
  5. Syncs `metrics_state.json` directly to **AWS S3** for ultra-fast (~15ms) web dashboard rendering.

---

# 4. Amazon DynamoDB Storage Layer

- **Table Name**: `EdgeDC360Telemetry`
- **Primary Key**:
  - **Partition Key**: `deviceId` (String, e.g. `Dublin-rack-01`, `STATE#Dublin-rack-01`)
  - **Sort Key**: `timestamp` (Number, Unix Epoch)
- **Features**:
  - Stores multi-sensor rack aggregates for historical auditing.
  - Stores operator alert acknowledgment state (`acknowledged: true/false`).

---

# 5. Amazon SNS (Simple Notification Service) Alerting

- **Topic Name**: `EdgeDC360CriticalAlerts`
- **Protocols**: Email / SMS Subscription
- **Alert Logic**:
  - Triggered when status is `CRITICAL` (e.g., sensor failure injected via `test_manual_sensor_failure.py`).
  - **Rate Limiting**: Cooldown period of 120 seconds between email dispatches.
  - **Silence Mechanism**: Operator click on `#btnAckAlert` sends `POST /api/acknowledge`, setting `"acknowledged": true` to silence subsequent alerts.

---

# 6. Amazon S3 & Web Hosting (Direct Live JSON Sync)

- **Bucket Name**: `edgedc360-dashboard-ajay`
- **Static Website Hosting**: Enabled (`index.html`)
- **Public Bucket Policy**: `GetObject` allowed for public read access.
- **Website Endpoint URL**:
  `http://edgedc360-dashboard-ajay.s3-website-us-east-1.amazonaws.com/dashboard/index.html`
- **Hosted Assets**:
  - `index.html` (Enterprise Operations Dashboard UI)
  - `styles.css` (Glassmorphism & Responsive Styles)
  - `app.js` (Real-Time Chart.js & Direct S3 Live JSON Sync Fetcher)
  - `metrics_state.json` (Live telemetry JSON synced directly by Lambda)

---

# 7. Amazon CloudWatch Monitoring

- **Log Group**: `/aws/lambda/lambda_handler`
- **Usage**: Diagnostic trace analysis, execution verification, and SNS dispatch auditing.

---

# 📈 Implementation Status Summary

| AWS Service | Configuration State | Operational Status |
| :--- | :--- | :--- |
| **AWS IoT Core** | Mutual TLS, `EdgeDC360Gateway`, Policy | **Active & Testing Passed** |
| **AWS IoT Rule** | `EdgeDC360TelemetryRule` $\rightarrow$ Lambda | **Active & Testing Passed** |
| **AWS Lambda** | Single `lambda_handler` Ingest Engine | **Active & Testing Passed** |
| **AWS DynamoDB** | `EdgeDC360Telemetry` Table | **Active & Testing Passed** |
| **AWS SNS** | `EdgeDC360CriticalAlerts` Topic | **Active & Testing Passed** |
| **AWS S3** | `edgedc360-dashboard-ajay` (Website + JSON Sync) | **Active & Testing Passed** |
| **AWS CloudWatch** | Execution & Error Tracing Logs | **Active & Testing Passed** |