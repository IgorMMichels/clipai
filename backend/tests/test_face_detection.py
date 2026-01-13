
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_face_detection")

sys.path.append(str(Path.cwd() / "backend"))

from services import resize_service

def test_face_detection():
    print("Testing Face Detection (OpenCV Robust Mode)...")
    video_path = Path("backend/uploads/real_test.mp4")
    
    if not video_path.exists():
        print(f"Video not found at {video_path}")
        return

    try:
        # Resize to 9:16 - this triggers the face detection logic
        # logic: returns crops_data with segments centered on face
        crops_data = resize_service.resize(video_path, aspect_ratio=(9, 16))
        
        print(f"Original Dimensions: {crops_data['original_width']}x{crops_data['original_height']}")
        print(f"Crop Dimensions: {crops_data['crop_width']}x{crops_data['crop_height']}")
        print(f"Segments found: {len(crops_data['segments'])}")
        
        if crops_data['segments']:
            print("First segment:", crops_data['segments'][0])
            print("Face detection seems to be working!")
        else:
            print("No segments found (or center crop fallback used).")
            
    except Exception as e:
        print(f"Face detection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_face_detection()
