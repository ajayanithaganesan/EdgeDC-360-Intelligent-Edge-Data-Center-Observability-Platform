# gateway/config.py

from pathlib import Path

ENDPOINT = "a2x07o92hx9u9p-ats.iot.us-east-1.amazonaws.com"

CLIENT_ID = "EdgeDC360Gateway"

TOPIC = "edgedc360/telemetry"

_BASE_DIR = Path(__file__).resolve().parents[1]

ROOT_CA = str(_BASE_DIR / "certificates" / "AmazonRootCA1.pem")

CERTIFICATE = str(_BASE_DIR / "certificates" / "device.pem.crt")

PRIVATE_KEY = str(_BASE_DIR / "certificates" / "private.pem.key")