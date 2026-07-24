# EdgeDC360 - AWS Backend Configuration (Current Progress)

> This document summarizes all AWS resources that have already been created and configured manually in the AWS Console. This serves as the current implementation state for continuing development in VS Code.

---

# Project Status

The following AWS backend has been successfully implemented and tested.

Current working pipeline:

```
Python Gateway
      │
      ▼
AWS IoT Core
      │
      ▼
IoT Rule
      │
      ▼
AWS Lambda
      │
      ▼
Amazon DynamoDB
```

The above pipeline is fully functional.

---

# AWS Region

```
us-east-1
```

---

# 1. AWS IoT Core

## IoT Thing

```
EdgeDC360Gateway
```

## Device Authentication

Created using:

- Auto-generated X.509 Certificate
- Private Key
- Device Certificate
- Amazon Root CA 1

Gateway connects using mutual TLS.

## IoT Policy

Policy Name

```
EdgeDC360Policy
```

Permissions

- iot:Connect
- iot:Publish
- iot:Subscribe
- iot:Receive

(Currently broad permissions for development.)

---

# MQTT Configuration

Client ID

```
EdgeDC360Gateway
```

Topic

```
edgedc360/telemetry
```

Endpoint

Configured in:

```
edge_gateway/config.py
```

Gateway publishes telemetry every 5 seconds.

Current payload:

```json
{
    "temperature": 30.5,
    "humidity": 55.2,
    "cpu": 68.3,
    "timestamp": 1784719000
}
```

---

# 2. AWS IoT Rule

Rule Name

```
EdgeDC360TelemetryRule
```

SQL

```sql
SELECT *
FROM 'edgedc360/telemetry'
```

SQL Version

```
2016-03-23
```

Action

```
Invoke Lambda Function
```

Lambda Function

```
EdgeDC360TelemetryProcessor
```

The IoT Rule automatically forwards every MQTT message to Lambda.

---

# 3. AWS Lambda

Function Name

```
EdgeDC360TelemetryProcessor
```

Runtime

```
Python 3.x
```

Purpose

Receives telemetry from AWS IoT Core.

Processes:

- Temperature
- Humidity
- CPU

Calculates device status

```
HEALTHY
WARNING
CRITICAL
```

Stores processed data into DynamoDB.

Important implementation detail:

DynamoDB requires floating-point values to be converted to `Decimal`.

---

# 4. Amazon DynamoDB

Table Name

```
EdgeDC360Telemetry
```

Primary Key

Partition Key

```
deviceId (String)
```

Sort Key

```
timestamp (Number)
```

Stored Item

```json
{
    "deviceId": "EdgeDC360Gateway",
    "timestamp": 1784719000,
    "temperature": 30.5,
    "humidity": 55.2,
    "cpu": 68.3,
    "status": "HEALTHY"
}
```

Every incoming telemetry message creates a new record because of the composite primary key.

---

# 5. Amazon CloudWatch

CloudWatch Logs are enabled for Lambda.

Used for:

- Lambda debugging
- Event verification
- Error logging

This was used to identify the DynamoDB float/Decimal issue.

---

# Current Project Architecture

```
Python Gateway
        │
        ▼
AWS IoT Core
        │
        ▼
IoT Rule
        │
        ▼
Lambda
        │
        ▼
DynamoDB
```

Current status:

- MQTT communication working
- IoT Rule working
- Lambda invocation working
- DynamoDB writes working
- CloudWatch logging working

---

# AWS Services Not Yet Implemented

The following services are intentionally postponed until the Fog Layer is completed.

- Amazon Kinesis
- Amazon SNS
- Amazon S3
- Amazon Managed Grafana
- Amazon Athena

---

# Important Architectural Decision

The AWS backend is considered complete for the current phase.

The next development phase is **Fog Computing**, not additional AWS services.

Upcoming implementation order:

1. Sensor Simulator
2. Edge Gateway
3. Rule Engine
4. Noise Filtering
5. Aggregation
6. Health Score Engine
7. SQLite Offline Buffer
8. AWS Publisher (reuse existing AWS backend)

Only after the Fog Layer is complete will the project continue with:

- Amazon Kinesis
- Amazon SNS
- Amazon S3
- Grafana Dashboards