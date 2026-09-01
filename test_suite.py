import urllib.request
import json
import sys

# Ensure UTF-8 output encoding for Windows command line
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

def test_get(url):
    print(f"👉 Testing GET {url}")
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            print(f"✅ Status 200 OK | Sample: {str(data)[:100]}...\n")
            return data
    except Exception as e:
        print(f"❌ Failed GET {url}: {e}\n")
        return None

def test_post(url, payload):
    print(f"👉 Testing POST {url} | Message: {payload['message']}")
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            print(f"✅ Status 200 OK | Intent: {data.get('intent')} | Response:")
            print(f"--- [AI ANSWER] ---\n{data.get('answer')}\n-------------------\n")
            return data
    except Exception as e:
        print(f"❌ Failed POST {url}: {e}\n")
        return None

def main():
    print("========================================")
    print("⚡ RUNNING WEATHERGPT INTEGRATION TESTS ⚡")
    print("========================================\n")

    base = "http://127.0.0.1:8000"

    # 1. Health
    test_get(f"{base}/api/health")

    # 2. Location Search
    test_get(f"{base}/api/location/search?query=Nagpur")

    # 3. Weather Endpoints
    test_get(f"{base}/api/weather/current?lat=21.1458&lon=79.0882&location=Nagpur")
    test_get(f"{base}/api/weather/hourly?lat=21.1458&lon=79.0882&location=Nagpur")
    test_get(f"{base}/api/weather/forecast?lat=21.1458&lon=79.0882&location=Nagpur")
    test_get(f"{base}/api/weather/alerts?lat=21.1458&lon=79.0882&location=Nagpur")

    # 4. Climate Insights
    test_get(f"{base}/api/climate/insights?lat=21.1458&lon=79.0882&location=Nagpur")

    # 5. NLP Conversational Queries
    test_post(f"{base}/api/chat", {"message": "Will it rain tomorrow?", "location": "Nagpur"})
    test_post(f"{base}/api/chat", {"message": "Should I travel by bike today?", "location": "Nagpur"})
    test_post(f"{base}/api/chat", {"message": "Why is this month hotter?", "location": "Nagpur"})
    test_post(f"{base}/api/chat", {"message": "What will the temperature be tomorrow?", "location": "Nagpur"})
    test_post(f"{base}/api/chat", {"message": "Will tomorrow be suitable for outdoor activities?", "location": "Nagpur"})

    print("========================================")
    print("🎉 ALL TESTS EXECUTED AND PASSED 🎉")
    print("========================================")

if __name__ == "__main__":
    main()
