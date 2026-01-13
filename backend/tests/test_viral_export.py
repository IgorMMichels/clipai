import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from services.editor import video_editor_service
from pathlib import Path
import subprocess
import json

def create_dummy_video(path: Path):
    # Create a 5s test video with color test source
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "testsrc=duration=5:size=1920x1080:rate=30",
        "-f", "lavfi", "-i", "sine=frequency=1000:duration=5",
        "-c:v", "libx264", "-c:a", "aac",
        str(path)
    ]
    subprocess.run(cmd, check=True, capture_output=True)

def test_export():
    input_path = Path("test_input.mp4")
    output_path = Path("test_output.mp4")
    
    try:
        print("Creating dummy video...")
        create_dummy_video(input_path)
        
        crops_data = {
            "crop_width": 1080,
            "crop_height": 1920,
            "segments": [
                {"start_time": 0, "end_time": 5, "x": 0, "y": 0} # Dummy crop
            ]
        }
        
        subtitles = [
            {"text": "Hello", "start_time": 0.5, "end_time": 1.5},
            {"text": "World", "start_time": 2.0, "end_time": 3.0}
        ]
        
        print("Running process_viral_clip...")
        video_editor_service.process_viral_clip(
            input_path=input_path,
            output_path=output_path,
            start_time=0,
            end_time=5,
            crops_data=crops_data,
            subtitles=subtitles,
            fps=60
        )
        
        if not output_path.exists():
            print("FAILED: Output file not created")
            return
            
        # Probe file
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_streams", str(output_path)
        ]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        data = json.loads(result.stdout)
        
        video_stream = next(s for s in data["streams"] if s["codec_type"] == "video")
        
        width = video_stream.get("width")
        height = video_stream.get("height")
        avg_frame_rate = video_stream.get("avg_frame_rate") # e.g. "60/1"
        
        print(f"Output Resolution: {width}x{height}")
        print(f"Output Frame Rate: {avg_frame_rate}")
        
        if width == 1080 and height == 1920 and avg_frame_rate == "60/1":
            print("SUCCESS: 1080x1920 @ 60fps")
        else:
            print("FAILED: Incorrect specs")

    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        # Cleanup
        if input_path.exists(): input_path.unlink()
        if output_path.exists(): output_path.unlink()

if __name__ == "__main__":
    test_export()
