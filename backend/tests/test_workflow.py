
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.append(str(Path.cwd() / "backend"))

from api.routes import upload, clips
from services import youtube_service, transcription_service, video_editor_service

async def test_workflow():
    print("Starting Workflow Test...")
    
    # Mock services to avoid external dependencies and heavy processing
    print("Mocking services...")
    youtube_service.download_video = MagicMock(return_value={
        "title": "Test Video",
        "duration": 600,
        "thumbnail": "http://example.com/thumb.jpg",
        "description": "Test Description"
    })
    
    transcription_service.transcribe = MagicMock(return_value={
        "text": "This is a test transcription for a viral video clip generator.",
        "language": "en",
        "start_time": 0.0,
        "end_time": 600.0,
        "sentences": [],
        "words": [],
        "_is_fallback": True
    })
    
    # Create a dummy video file for file existence checks
    dummy_video_path = Path("backend/uploads/test_video.mp4")
    dummy_video_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dummy_video_path, "wb") as f:
        f.write(b"dummy video content")
        
    # Mock file operations where necessary
    video_editor_service.generate_preview = MagicMock(return_value=Path("backend/outputs/test_job/preview.mp4"))
    
    # 1. Upload YouTube Video
    print("\n1. Testing YouTube Upload...")
    from models.schemas import YouTubeUploadRequest
    from fastapi import BackgroundTasks
    
    req = YouTubeUploadRequest(url="https://youtube.com/watch?v=123")
    bg_tasks = BackgroundTasks()
    
    # We need to simulate the background task execution
    response = await upload.upload_youtube(req, bg_tasks)
    job_id = response.id
    print(f"Job ID: {job_id}")
    
    # Manually trigger background task
    print("Running background task...")
    # Update job path to dummy file manually for test
    upload.jobs[job_id]["original_path"] = str(dummy_video_path)
    
    await upload.process_youtube_job(job_id, req.url)
    
    # 2. Check Status
    print("\n2. Checking Status...")
    job = upload.jobs[job_id]
    print(f"Status: {job['status']}")
    print(f"Clips found: {len(job['clips'])}")
    
    if len(job['clips']) > 0:
        print(f"First clip score: {job['clips'][0].get('score')}")
        if job['clips'][0].get('score') is None:
             print("FAIL: Clip missing score")
             return
    else:
        print("FAIL: No clips found")
        return

    # 3. Generate Preview
    print("\n3. Testing Preview Generation...")
    clip_id = job['clips'][0]['id']
    
    # Mock existence of output dir/file for the route check
    output_dir = Path(f"backend/outputs/{job_id}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Execute preview route
    preview_res = await clips.generate_preview(job_id, clip_id)
    print(f"Preview Response: {preview_res}")
    
    if preview_res["status"] == "ready":
        print("SUCCESS: Workflow Test Passed!")
    else:
        print("FAIL: Preview generation failed")

if __name__ == "__main__":
    asyncio.run(test_workflow())
