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
* Visualize infrastructure health using Enterprise Web Dashboard
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
                      +-----------v-----------+
                      |     Edge Gateway      |
                      |-----------------------|
                      | MQTT Subscriber       |
                      | Rule Engine           |
                      | Stream Processor      |
                      | Batch Processor       |
                      | Health Score Engine   |
                      | SQLite Offline Buffer |
                      | AWS Publisher         |
                      +-----------+-----------+
                                  |
                                  | Mutual TLS (MQTT)
                                  v
                             AWS IoT Core
                                  |
                               IoT Rule ──(Error Action Fallback)──► Amazon SQS Queue
                                  |
                             AWS Lambda
                     +------------+------------+
                     |            |            |
                     v            v            v
                 DynamoDB     Amazon SNS    Amazon S3
               (Telemetry)    (Alerts)    (JSON Sync)
                                               |
                                               v
                                        S3 Web Dashboard
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
AWS Lambda
    ↓
DynamoDB & Amazon S3
    ↓
Amazon SNS & S3 Dashboard
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
AWS Lambda
    ↓
Amazon S3
    ↓
S3 Web Dashboard
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
| Amazon SQS                 | Error Action Fallback Queue|
| AWS Lambda                 | Core event processing      |
| Amazon DynamoDB            | Real-time operational data |
| Amazon S3                  | Web hosting & JSON sync    |
| Amazon SNS                 | Critical alert notifications |
| Amazon CloudWatch          | Operational monitoring     |

---

# 📁 Repository Structure

```text
EdgeDC360/
│
├── sensor_simulator/
├── edge_gateway/
├── dashboard/
├── shared/
├── certificates/
├── docs/
├── .github/
│   └── workflows/
│
├── scripts/
│   ├── run_live_gateway.py
│   └── test_manual_sensor_failure.py
├── lambda_handler.py
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

### Object Storage & Web Hosting

* Amazon S3

### Monitoring

* CloudWatch

### Alerting

* Amazon SNS

### Dashboard

* HTML5 / CSS3 / JavaScript (Chart.js)

### Version Control

* Git & GitHub

### CI

* GitHub Actions

---

# 🚀 Getting Started

## Clone the repository

```bash
git clone https://github.com/ajayanithaganesan/EdgeDC360.git
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

## Run Live AWS Gateway

Run the live gateway with configurable sampling and dispatch intervals:

```powershell
python .\scripts\run_live_gateway.py --sample-interval 2 --batch-interval 10
```

## Run Manual Failure Injection Test

Inject a critical temperature failure to test SNS alerts and dashboard updating:

```powershell
python .\scripts\test_manual_sensor_failure.py --site Dublin --rack rack-01 --sensor temperature --value 88.0
```

---

# 🎯 Project Status

| Component        | Status |
| ---------------- | ------ |
| Project Setup    | ✅      |
| Sensor Simulator | ✅      |
| Edge Gateway     | ✅      |
| AWS Backend      | ✅      |
| S3 Web Dashboard | ✅      |
| Documentation    | ✅      |

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
