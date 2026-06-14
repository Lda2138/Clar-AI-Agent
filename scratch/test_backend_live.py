import urllib.request
import json
import time

def test_live_api():
    url = "http://127.0.0.1:8001/api/radar/track"
    # Using non-default parameters (threshold_offset=29.5 instead of 30) to bypass the startup cache
    payload = {
        "Pf": 0.0001,
        "R_ref": 4,
        "R_pro": 2,
        "drop_high_num": 10,
        "threshold_offset": 29.5,
        "qs": 0.01,
        "gate_dist": 16.0,
        "amp_drop_tol": 8.0
    }
    
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
    
    print("Sending live request to /api/radar/track with custom parameters (offset=29.5)...")
    for i in range(3):
        t0 = time.time()
        try:
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                t1 = time.time()
                print(f"Request {i+1}: status={response.status}, time={t1 - t0:.4f}s, confirmed_paths={len(res_data['confirmed_paths'])}")
        except Exception as e:
            print(f"Request {i+1} FAILED:", e)
            
    print("Live verification finished!")

if __name__ == "__main__":
    test_live_api()
