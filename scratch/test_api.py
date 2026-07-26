import urllib.request
import urllib.error

url = "https://yj0hurjgfl.execute-api.us-east-1.amazonaws.com/EdgeDC360GetMetrics"
req = urllib.request.Request(url, headers={
    "Origin": "http://edgedc360-dashboard-ajay.s3-website-us-east-1.amazonaws.com"
})

try:
    with urllib.request.urlopen(req) as resp:
        print("STATUS:", resp.status)
        print("CORS HEADER:", resp.headers.get("Access-Control-Allow-Origin"))
        data = resp.read().decode('utf-8')
        print("BODY LENGTH:", len(data))
except urllib.error.HTTPError as err:
    print("HTTP ERROR CODE:", err.code)
    print("HTTP ERROR BODY:", err.read().decode('utf-8'))
except Exception as e:
    print("ERROR:", e)
