import sys
import os
# Ensure root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models import RadarParams
from backend.radar_routes import api_radar_track, api_radar_frame

def test_radar_tracking():
    print("Testing api_radar_track...")
    params = RadarParams()
    result = api_radar_track(params)
    
    assert "confirmed_paths" in result, "Missing confirmed_paths"
    assert "false_alarms" in result, "Missing false_alarms"
    assert "misses" in result, "Missing misses"
    assert "stats" in result, "Missing stats"
    assert "step_calculations" in result, "Missing step_calculations"
    
    print("API output statistics:")
    print(result["stats"])
    
    print("Step calculations count:", len(result["step_calculations"]))
    if len(result["step_calculations"]) > 0:
        print("First calculation sample keys:", result["step_calculations"][0].keys())
        
    print("Testing api_radar_frame...")
    frame_result = api_radar_frame(1)
    assert frame_result["frame_idx"] == 1
    assert len(frame_result["z"]) == 250
    assert len(frame_result["z"][0]) == 250
    print("Frame 1 dimensions: {}x{}".format(len(frame_result["z"]), len(frame_result["z"][0])))
    print("All tests passed successfully!")

if __name__ == "__main__":
    test_radar_tracking()
