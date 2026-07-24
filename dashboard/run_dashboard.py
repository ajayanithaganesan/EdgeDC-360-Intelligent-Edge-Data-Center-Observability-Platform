import http.server
import json
import socketserver
from pathlib import Path

PORT = 8000
DASHBOARD_DIR = Path(__file__).parent.resolve()
WORKSPACE_DIR = DASHBOARD_DIR.parent
METRICS_FILE = WORKSPACE_DIR / "metrics_state.json"

class DashboardRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DASHBOARD_DIR), **kwargs)

    def do_GET(self):
        if self.path == "/api/metrics":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            target_file = METRICS_FILE
            if not target_file.exists():
                scripts_file = WORKSPACE_DIR / "scripts" / "metrics_state.json"
                if scripts_file.exists():
                    target_file = scripts_file

            if target_file.exists():
                try:
                    with open(target_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self.wfile.write(json.dumps(data).encode("utf-8"))
                    return
                except Exception:
                    pass

            # Fallback default structure if gateway has not run yet
            fallback_data = {
                "racks": {},
                "fog": {
                    "generated": 0,
                    "filtered": 0,
                    "uploaded": 0,
                    "bandwidth_saved": 88.4,
                    "latency": 11.8
                },
                "history": {
                    "timestamps": [],
                    "temperature": [],
                    "cooling": [],
                    "power": [],
                    "ups": []
                }
            }
            self.wfile.write(json.dumps(fallback_data).encode("utf-8"))
            return

        super().do_GET()

def run():
    print(f"==================================================")
    print(f" EDGE DC360 - ENTERPRISE DASHBOARD SERVER")
    print(f"==================================================")
    print(f" Serving dashboard from: {DASHBOARD_DIR}")
    print(f" Reading telemetry from: {METRICS_FILE}")
    print(f" Dashboard available at: http://localhost:{PORT}")
    print(f" Press Ctrl+C to stop the server")
    print(f"==================================================")
    
    with socketserver.TCPServer(("", PORT), DashboardRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down dashboard server...")

if __name__ == "__main__":
    run()
