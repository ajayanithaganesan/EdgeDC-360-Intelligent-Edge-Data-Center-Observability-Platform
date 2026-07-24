"""
Lightweight HTTP and static file server for the EdgeDC360 Custom HTML Dashboard.
Serves static assets from dashboard/ and outputs JSON metrics for real-time Web UI polling.

Usage:
    .\.venv\Scripts\python.exe .\scripts\run_dashboard.py
"""

import http.server
import json
import os
import socketserver
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PORT = 8000
DASHBOARD_DIR = ROOT / "dashboard"
METRICS_FILE = ROOT / "metrics_state.json"


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Override directory to serve static dashboard assets
        super().__init__(*args, directory=str(DASHBOARD_DIR), **kwargs)

    def do_GET(self):
        if self.path == "/api/metrics":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            # Read metrics state file
            metrics_data = self._read_metrics_state()
            self.wfile.write(json.dumps(metrics_data).encode("utf-8"))
        else:
            super().do_GET()

    def _read_metrics_state(self) -> dict:
        if METRICS_FILE.exists():
            try:
                with open(METRICS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Append calculated executive fields dynamically
                racks = data.get("racks", {})
                total_racks = len(racks)
                
                if total_racks > 0:
                    health_scores = [r.get("health_score", 100) for r in racks.values()]
                    overall_health = int(sum(health_scores) / total_racks)
                    
                    active_alerts = sum(1 for r in racks.values() if r.get("health_state") == "critical")
                    active_warnings = sum(1 for r in racks.values() if r.get("health_state") == "warning")
                else:
                    overall_health = 100
                    active_alerts = 0
                    active_warnings = 0

                data["exec"] = {
                    "overall_health": overall_health,
                    "active_alerts": active_alerts,
                    "active_warnings": active_warnings
                }
                return data
            except Exception as e:
                print(f"Error reading metrics_state.json: {e}")

        # Fallback dummy metrics data if gateway runner has not started
        return {
            "racks": {
                "Dublin-rack-01": {
                    "site": "Dublin", "rack_id": "rack-01", "health_score": 95, "health_state": "healthy",
                    "sensors": {
                        "temperature": {"value": 24.1, "unit": "C", "status": "healthy"},
                        "humidity": {"value": 45.2, "unit": "%", "status": "healthy"},
                        "power": {"value": 380, "unit": "W", "status": "healthy"},
                        "ups": {"value": 96.0, "unit": "%", "status": "healthy"},
                        "cooling": {"value": 2350, "unit": "RPM", "status": "healthy"}
                    }
                },
                "Dublin-rack-02": {
                    "site": "Dublin", "rack_id": "rack-02", "health_score": 98, "health_state": "healthy",
                    "sensors": {
                        "temperature": {"value": 23.5, "unit": "C", "status": "healthy"},
                        "humidity": {"value": 44.0, "unit": "%", "status": "healthy"},
                        "power": {"value": 370, "unit": "W", "status": "healthy"},
                        "ups": {"value": 98.0, "unit": "%", "status": "healthy"},
                        "cooling": {"value": 2400, "unit": "RPM", "status": "healthy"}
                    }
                },
                "Cork-rack-01": {
                    "site": "Cork", "rack_id": "rack-01", "health_score": 75, "health_state": "warning",
                    "sensors": {
                        "temperature": {"value": 31.2, "unit": "C", "status": "degraded"},
                        "humidity": {"value": 52.0, "unit": "%", "status": "healthy"},
                        "power": {"value": 420, "unit": "W", "status": "healthy"},
                        "ups": {"value": 85.0, "unit": "%", "status": "healthy"},
                        "cooling": {"value": 1800, "unit": "RPM", "status": "degraded"}
                    }
                },
                "Cork-rack-02": {
                    "site": "Cork", "rack_id": "rack-02", "health_score": 85, "health_state": "healthy",
                    "sensors": {
                        "temperature": {"value": 25.4, "unit": "C", "status": "healthy"},
                        "humidity": {"value": 46.5, "unit": "%", "status": "healthy"},
                        "power": {"value": 395, "unit": "W", "status": "healthy"},
                        "ups": {"value": 94.0, "unit": "%", "status": "healthy"},
                        "cooling": {"value": 2200, "unit": "RPM", "status": "healthy"}
                    }
                },
                "Galway-rack-01": {
                    "site": "Galway", "rack_id": "rack-01", "health_score": 38, "health_state": "critical",
                    "sensors": {
                        "temperature": {"value": 38.5, "unit": "C", "status": "failed"},
                        "humidity": {"value": 62.0, "unit": "%", "status": "healthy"},
                        "power": {"value": 580, "unit": "W", "status": "degraded"},
                        "ups": {"value": 91.0, "unit": "%", "status": "healthy"},
                        "cooling": {"value": 950, "unit": "RPM", "status": "failed"}
                    }
                },
                "Galway-rack-02": {
                    "site": "Galway", "rack_id": "rack-02", "health_score": 99, "health_state": "healthy",
                    "sensors": {
                        "temperature": {"value": 22.8, "unit": "C", "status": "healthy"},
                        "humidity": {"value": 44.5, "unit": "%", "status": "healthy"},
                        "power": {"value": 365, "unit": "W", "status": "healthy"},
                        "ups": {"value": 99.0, "unit": "%", "status": "healthy"},
                        "cooling": {"value": 2450, "unit": "RPM", "status": "healthy"}
                    }
                }
            },
            "fog": {
                "generated": 1420,
                "filtered": 1210,
                "uploaded": 210,
                "bandwidth_saved": 85.2,
                "latency": 4
            },
            "exec": {
                "overall_health": 81,
                "active_alerts": 1,
                "active_warnings": 1
            },
            "history": {
                "timestamps": [
                    "2026-07-24T16:00:00Z", "2026-07-24T16:05:00Z", "2026-07-24T16:10:00Z",
                    "2026-07-24T16:15:00Z", "2026-07-24T16:20:00Z", "2026-07-24T16:25:00Z",
                    "2026-07-24T16:30:00Z"
                ],
                "temperature": [22.5, 23.1, 23.8, 24.5, 25.1, 24.3, 24.1],
                "cooling": [2450, 2400, 2350, 2300, 2250, 2350, 2350],
                "power": [365, 370, 375, 385, 390, 380, 380],
                "ups": [99.0, 98.5, 98.0, 97.0, 96.5, 96.0, 96.0]
            }
        }


def main():
    # Ensure dashboard folder exists
    if not DASHBOARD_DIR.exists():
        print(f"Error: Dashboard folder not found at {DASHBOARD_DIR}")
        return 1

    handler = DashboardHandler
    # Allow port reuse to avoid address already in use errors
    socketserver.TCPServer.allow_reuse_address = True

    try:
        with socketserver.TCPServer(("", PORT), handler) as httpd:
            print("==================================================")
            print(" EDGE DC360 - WEB OPERATIONS DASHBOARD")
            print("==================================================")
            print(f" Local Web Server Running: http://localhost:{PORT}")
            print(f" Static files root:       {DASHBOARD_DIR}")
            print(f" Metrics State File:      {METRICS_FILE}")
            print(" Press Ctrl+C to stop.")
            print("==================================================")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Dashboard Web Server...")
    except Exception as e:
        print(f"Server Error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
