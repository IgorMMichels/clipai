
import asyncio
import sys
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_stacked")

sys.path.append(str(Path.cwd() / "backend"))

from services import video_editor_service, resize_service

def test_stacked_layout():
    print("Testing Stacked Layout...")
    output_dir = Path("backend/outputs/test_integration")
    input_path = output_dir / "temp_trimmed.mp4" # Use the trimmed clip from previous test
    output_path = output_dir / "test_stacked.mp4"
    
    if not input_path.exists():
        print("Input file not found. Run real_test.py first.")
        return

    # Mock crops data (since we know it works from previous test)
    # Just center crop for simplicity of testing the layout function
    crops_data = {
        "crop_width": 360, # Arbitrary small width
        "crop_height": 360, # Square for face
        "segments": [
            {"x": 0, "y": 0, "start_time": 0, "end_time": 100} # Full duration
        ]
    }
    
    try:
        video_editor_service.apply_stacked_layout(
            input_path,
            output_path,
            crops_data
        )
        print(f"Stacked video saved to: {output_path}")
    except Exception as e:
        print(f"Stacked layout failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_stacked_layout()
