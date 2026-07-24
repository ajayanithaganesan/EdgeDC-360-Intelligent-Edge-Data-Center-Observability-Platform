# 🚀 EdgeDC360

> **Enterprise Edge Data Center Operations Platform using Fog Computing and AWS**

EdgeDC360 is an enterprise-inspired Fog and Edge Computing platform that simulates a modern data center monitoring solution. It demonstrates how intelligent edge processing can reduce bandwidth consumption, minimize latency, improve resiliency, and enable scalable cloud analytics using AWS.

The project was developed as part of the MSc Cloud Computing **Fog & Edge Computing** module and follows a real-world distributed architecture consisting of **Sensor Layer → Fog Layer → Cloud Layer → Analytics Dashboard**.

---

# 📖 Project Overview

Modern data centers generate enormous amounts of telemetry every second. Sending every sensor reading directly to the cloud is inefficient, expensive, and introduces unnecessary latency.

EdgeDC360 solves this problem by introducing a **Fog Node (Edge Gateway)** that performs local processing before forwarding only meaningful data to AWS.

The platform demonstrates:

* Edge/Fog Computing
* Real-Time Event Processing
* Batch Processing
* Event-Driven Architecture
* AWS Serverless Backend
* IoT Data Streaming
* Real-Time Infrastructure Monitoring
* Historical Analytics

---

# 🎯 Project Objectives

* Simulate realistic data center sensors
* Perform intelligent processing at the edge
* Demonstrate bandwidth reduction through Fog Computing
* Build a scalable cloud backend using AWS
* Store real-time and historical telemetry
* Visualize infrastructure health using Grafana
* Showcase an enterprise-grade distributed architecture

---

# 🏢 Business Scenario

A cloud service provider operates multiple enterprise data centers located across Ireland.

Each data center contains multiple server racks equipped with environmental and infrastructure sensors.

Instead of continuously sending every sensor reading to the cloud, an **Edge Gateway** installed inside each data center performs local processing.

The gateway:

* Filters unnecessary readings
* Detects anomalies
* Aggregates sensor data
* Buffers data during network failures
* Prioritizes critical alerts
* Sends processed telemetry to AWS

This architecture reduces cloud traffic while maintaining real-time visibility into infrastructure health.

---

# 🏗️ System Architecture

```text
                    +---------------------------+
                    |   Sensor Simulator        |
                    |---------------------------|
                    | Temperature               |
                    | Humidity                  |
                    | Power Consumption         |
                    | UPS Battery               |
                    | Cooling Unit              |
                    +-------------+-------------+
                                  |
                                  | MQTT
                                  |
                     +------------v------------+
                     |      Edge Gateway       |
                     |-------------------------|
                     | MQTT Subscriber         |
                     | Rule Engine             |
                     | Stream Processor        |
                     | Batch Processor         |
                     | Health Score Engine     |
                     | SQLite Offline Buffer   |
                     | AWS Publisher           |
                     +------------+------------+
                                  |
                                  |
                           AWS IoT Core
                                  |
                           Amazon Kinesis
                    +-------------+--------------+
                    |                            |
              Realtime Pipeline           Batch Pipeline
                    |                            |
              AWS Lambda                  Amazon S3
                    |                            |
              DynamoDB                    Athena (Optional)
                    |                            |
              Grafana Dashboard          Historical Analytics
                    |
              Amazon SNS Alerts
```

---

# 🧠 Why Fog Computing?

Instead of uploading every sensor reading, the Edge Gateway performs intelligent processing locally.

### Edge Processing

* Noise filtering
* Rule-based anomaly detection
* Aggregation
* Local health score calculation
* Offline buffering
* Priority-based forwarding

### Cloud Processing

* Long-term storage
* Historical analytics
* Real-time dashboards
* Alert notifications
* Capacity planning
* Infrastructure reporting

---

# ⚙️ Simulated Sensors

The platform simulates five different data center sensors.

| Sensor                     | Purpose                     |
| -------------------------- | --------------------------- |
| 🌡 Rack Temperature        | Monitor rack temperature    |
| 💧 Rack Humidity           | Monitor humidity levels     |
| ⚡ Server Power Consumption | Monitor electrical usage    |
| 🔋 UPS Battery Health      | Monitor battery status      |
| 🌀 Cooling Unit Status     | Monitor fan RPM and airflow |

Each sensor supports:

* Configurable sampling frequency
* Configurable publishing frequency
* Trend simulation
* Random values
* Anomaly injection

---

# 🖥️ Edge Gateway Features

The Edge Gateway is the core component of the project.

Responsibilities include:

* MQTT Subscriber
* Message Validation
* Rule Engine
* Stream Processing
* Batch Processing
* SQLite Offline Storage
* Health Score Calculation
* AWS Publisher

---

# ⚡ Real-Time Processing

Critical events are processed immediately.

Examples include:

* High rack temperature
* UPS failure
* Cooling failure
* Excessive power usage
* Dangerous humidity levels

Real-time flow:

```text
Sensor
    ↓
Edge Gateway
    ↓
AWS IoT Core
    ↓
Amazon Kinesis
    ↓
AWS Lambda
    ↓
DynamoDB
    ↓
Grafana
    ↓
Amazon SNS
```

---

# 📊 Batch Processing

Normal telemetry is aggregated every configurable interval before being uploaded.

The Edge Gateway calculates:

* Average
* Minimum
* Maximum
* Standard Deviation

instead of sending every raw reading.

Batch flow:

```text
Sensor
    ↓
Edge Gateway
    ↓
AWS IoT Core
    ↓
Amazon Kinesis
    ↓
Amazon S3
    ↓
Athena (Optional)
    ↓
Grafana
```

---

# 📈 Dashboards

The platform provides four dashboards.

## 1. Live Operations Dashboard

Displays:

* Temperature
* Humidity
* UPS Status
* Cooling Status
* Power Consumption
* Rack Health

---

## 2. Fog Computing Dashboard

Shows the benefits of edge processing.

Metrics include:

* Messages Generated
* Messages Filtered
* Messages Uploaded
* Edge Latency
* Estimated Bandwidth Savings

---

## 3. Infrastructure Analytics Dashboard

Historical trends:

* Temperature
* Cooling efficiency
* Energy consumption
* UPS performance

---

## 4. Executive Dashboard

High-level KPIs:

* Overall infrastructure health
* Active alerts
* Warning count
* Estimated bandwidth savings
* System availability

---

# ☁️ AWS Services

The platform uses the following AWS services.

| Service                    | Purpose                    |
| -------------------------- | -------------------------- |
| AWS IoT Core               | IoT device connectivity    |
| Amazon Kinesis             | Real-time streaming        |
| AWS Lambda                 | Event processing           |
| Amazon DynamoDB            | Real-time operational data |
| Amazon S3                  | Historical storage         |
| Amazon SNS                 | Alert notifications        |
| Amazon CloudWatch          | Monitoring                 |
| Grafana                    | Visualization              |
| Amazon Athena *(Optional)* | Historical querying        |

---

# 📁 Repository Structure

```text
EdgeDC360/
│
├── sensor_simulator/
├── edge_gateway/
├── cloud/
├── dashboard/
├── shared/
├── docs/
├── .github/
│   └── workflows/
│
├── requirements.txt
├── config.py
├── .env.example
├── README.md
└── LICENSE
```

---

# 🛠️ Technology Stack

### Programming

* Python

### Messaging

* MQTT

### Edge Storage

* SQLite

### Cloud

* AWS

### Database

* DynamoDB

### Object Storage

* Amazon S3

### Streaming

* Amazon Kinesis

### Monitoring

* CloudWatch

### Dashboard

* Grafana

### Version Control

* Git & GitHub

### CI

* GitHub Actions

---

# 🚀 Getting Started

## Clone the repository

```bash
git clone https://github.com/<your-username>/EdgeDC360.git
cd EdgeDC360
```

## Create a virtual environment

```bash
python -m venv .venv
```

## Activate the environment

Windows

```powershell
.venv\Scripts\activate
```

Linux / macOS

```bash
source .venv/bin/activate
```

## Install dependencies

```bash
pip install -r requirements.txt
```

## Configure environment variables

Copy:

```text
.env.example
```

to

```text
.env
```

Update the values according to your AWS configuration.

## Run a local MQTT smoke test on Windows

If you have Docker Desktop installed, you can run the broker, gateway, and simulator together with one command:

```powershell
.\scripts\run_mqtt_smoke_test.ps1
```

Optional arguments:

```powershell
.\scripts\run_mqtt_smoke_test.ps1 -Cycles 5 -Sleep 1
```

This script:

- Starts a local Mosquitto broker in Docker
- Launches the edge gateway in MQTT mode
- Runs the sensor simulator against the broker
- Cleans everything up afterward

## Run without Docker

If you do not want Docker, use the no-broker smoke test instead:

```powershell
python .\scripts\run_local_smoke_test.py
```

Optional:

```powershell
python .\scripts\run_local_smoke_test.py --cycles 3
python .\scripts\run_local_smoke_test.py --buffer-offline
```

This verifies:

- Sensor generation
- JSON serialization and parsing
- Edge processing
- Health scoring
- Optional SQLite buffering

This is the recommended next step if you want to keep moving without a broker.

---

# 🎯 Project Status

| Component        | Status |
| ---------------- | ------ |
| Project Setup    | ✅      |
| Sensor Simulator | 🚧 scaffolded |
| Edge Gateway     | 🚧 scaffolded |
| AWS Backend      | 🚧     |
| Dashboards       | 🚧     |
| Documentation    | 🚧 updating |

---

# 📚 Learning Outcomes

This project demonstrates practical experience with:

* Fog Computing
* Edge Computing
* Distributed Systems
* Event-Driven Architecture
* AWS IoT Services
* Real-Time Data Processing
* Batch Processing
* Cloud-Native Applications
* Infrastructure Monitoring
* IoT Analytics

---

# 📄 License

This project is licensed under the MIT License.

---

## 👨‍💻 Author

**Ajay Anitha Ganesan**

MSc Cloud Computing
National College of Ireland
