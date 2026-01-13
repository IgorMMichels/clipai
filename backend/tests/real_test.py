
import asyncio
import sys
import os
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test")

# Add backend to path
sys.path.append(str(Path.cwd() / "backend"))

from services import youtube_service, transcription_service, clip_finder_service, resize_service, video_editor_service

async def run_integration_test():
    print("="*50)
    print("STARTING REAL INTEGRATION TEST")
    print("="*50)
    
    output_dir = Path("backend/outputs/test_integration")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Download Video
    print("\n[1] Downloading Video...")
    video_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw" # Me at the zoo (18s)
    video_path = output_dir / "input.mp4"
    
    try:
        info = youtube_service.download_video(video_url, video_path)
        print(f"Downloaded: {info['title']}")
    except Exception as e:
        print(f"Download failed: {e}")
        return

    # 2. Transcribe (Real WhisperX)
    print("\n[2] Transcribing (WhisperX)...")
    try:
        transcription = transcription_service.transcribe(video_path, language="en")
        print(f"Transcription length: {len(transcription['text'])}")
        print(f"Text sample: {transcription['text'][:100]}...")
        print(f"Sentences: {len(transcription['sentences'])}")
    except Exception as e:
        print(f"Transcription failed: {e}")
        return

    # 3. Find Clips (Custom Heuristic)
    print("\n[3] Finding Clips...")
    # Force min_duration small for this short video
    clips = clip_finder_service.find_clips(transcription, min_duration=5.0, max_duration=15.0)
    print(f"Found {len(clips)} clips")
    if clips:
        print(f"Top clip score: {clips[0]['score']}")
        print(f"Top clip text: {clips[0]['transcript']}")
    else:
        print("No clips found! Creating a manual fallback clip for testing rest of pipeline.")
        clips = [{
            "id": "manual_test_clip",
            "start_time": 0.0,
            "end_time": 10.0,
            "duration": 10.0,
            "transcript": transcription["text"][:50],
            "score": 80.0
        }]

    # 4. Resize (Mediapipe)
    print("\n[4] Resizing/Analysis (Mediapipe)...")
    # Using the first clip or the whole video for analysis
    # Note: Resize service takes the full video usually, but we crop to the clip time later
    # Here we just test the resize service on the input video to see if it generates segments
    try:
        crops = resize_service.resize(video_path, aspect_ratio=(9, 16))
        print(f"Resize segments found: {len(crops['segments'])}")
    except Exception as e:
        print(f"Resize failed: {e}")
        return

    # 5. Export (MoviePy/FFmpeg)
    print("\n[5] Exporting Clip...")
    clip_data = clips[0]
    clip_out_path = output_dir / "final_clip.mp4"
    
    try:
        # A. Trim
        trimmed_path = output_dir / "temp_trimmed.mp4"
        video_editor_service.trim_clip(
            video_path, trimmed_path, 
            clip_data["start_time"], clip_data["end_time"]
        )
        print("Trimmed.")
        
        # B. Resize (using the crops data we got, but we need crops relative to the clip?)
        # Actually resize_service analyzes the whole video in my implementation?
        # Wait, if we trim first, we should analyze the trimmed video.
        # Let's analyze the trimmed video for accuracy in this test.
        
        print("Analyzing trimmed clip for resize...")
        crops_trimmed = resize_service.resize(trimmed_path, aspect_ratio=(9, 16))
        
        # C. Apply Resize
        resized_path = output_dir / "temp_resized.mp4"
        video_editor_service.resize_video(trimmed_path, resized_path, crops_trimmed)
        print("Resized.")
        
        # D. Add Subtitles
        # Fake subtitles for test
        subs = [{"text": "Test Subtitle", "start_time": 0, "end_time": 2}]
        video_editor_service.add_subtitles(resized_path, clip_out_path, subs)
        print(f"Final export saved to: {clip_out_path}")
        
    except Exception as e:
        print(f"Export failed: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\nTEST COMPLETE: SUCCESS")

if __name__ == "__main__":
    asyncio.run(run_integration_test())
