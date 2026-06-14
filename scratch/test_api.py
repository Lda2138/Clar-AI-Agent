import urllib.request
import json

def test_api():
    print("Testing /api/signal/generate...")
    data = {
        "signal_type": "正弦+白噪声",
        "freq": 200.0,
        "fs": 10000,
        "snr_db": 10.0,
        "duration": 0.4
    }
    req = urllib.request.Request(
        "http://127.0.0.1:8001/api/signal/generate",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    res = urllib.request.urlopen(req)
    res_data = json.loads(res.read().decode("utf-8"))
    print("Keys in response:", list(res_data.keys()))
    assert "t" in res_data
    assert "clean" in res_data
    assert "noisy" in res_data
    assert "features" in res_data
    print("Signal generate: PASS")

    print("Testing /api/signal/filter...")
    filter_data = {
        "signal_type": "正弦+白噪声",
        "freq": 200.0,
        "fs": 10000,
        "snr_db": 10.0,
        "duration": 0.4,
        "filter_type": "moving_average",
        "window_size": 10,
        "cutoff_freq": 500.0
    }
    req_filt = urllib.request.Request(
        "http://127.0.0.1:8001/api/signal/filter",
        data=json.dumps(filter_data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    res_filt = urllib.request.urlopen(req_filt)
    res_filt_data = json.loads(res_filt.read().decode("utf-8"))
    print("Keys in filter response:", list(res_filt_data.keys()))
    assert "filtered" in res_filt_data
    assert "features" in res_filt_data
    print("Signal filter: PASS")

if __name__ == "__main__":
    test_api()
