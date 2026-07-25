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

    def do_POST(self):
        if self.path == "/api/acknowledge":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            
            try:
                payload = json.loads(body.decode("utf-8")) if body else {}
                rack_id = payload.get("rack_id", "all")
                
                target_file = METRICS_FILE
                if not target_file.exists():
                    scripts_file = WORKSPACE_DIR / "scripts" / "metrics_state.json"
                    if scripts_file.exists():
                        target_file = scripts_file

                data = {}
                if target_file.exists():
                    try:
                        with open(target_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                    except Exception:
                        pass

                racks = data.get("racks", {})
                if rack_id == "all" or rack_id.lower() == "global":
                    for rk in racks:
                        racks[rk]["acknowledged"] = True
                elif rack_id in racks:
                    racks[rack_id]["acknowledged"] = True
                else:
                    # Match case-insensitively
                    for rk in racks:
                        if rk.lower() == rack_id.lower():
                            racks[rk]["acknowledged"] = True

                # Also update anomaly_active.json if present
                anomaly_file = WORKSPACE_DIR / "anomaly_active.json"
                if anomaly_file.exists():
                    try:
                        with open(anomaly_file, "r", encoding="utf-8") as af:
                            a_data = json.load(af)
                        a_data["acknowledged"] = True
                        with open(anomaly_file, "w", encoding="utf-8") as af:
                            json.dump(a_data, af)
                    except Exception:
                        pass

                with open(target_file, "w", encoding="utf-8") as f:
                    json.dump(data, f)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "acknowledged", "rack_id": rack_id}).encode("utf-8"))
                return
            except Exception as exc:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(exc)}).encode("utf-8"))
                return

        super().do_POST()

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
