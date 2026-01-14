"""
Video Upload API Routes
Enhanced with multi-platform support and AI features
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from pathlib import Path
from typing import Optional
import uuid
import shutil
import aiofiles
import json
import asyncio

from config import settings
from models.schemas import VideoUploadRequest, YouTubeUploadRequest, URLUploadRequest, VideoJobResponse, ProcessingStatus
from services import video_downloader_service

router = APIRouter(prefix="/upload", tags=["Upload"])

# In-memory job storage (use Redis/DB in production)
jobs = {}


@router.post("/", response_model=VideoJobResponse)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    language: Optional[str] = None,
    aspect_ratio_w: int = 9,
    aspect_ratio_h: int = 16,
    generate_description: bool = True,
    description_language: str = "en",
):
    """
    Upload a video for processing
    
    - Accepts video files (mp4, mov, avi, mkv, webm)
    - Returns a job ID to track progress
    """
    # Validate file type
    allowed_types = ["video/mp4", "video/quicktime", "video/x-msvideo", "video/x-matroska", "video/webm"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: mp4, mov, avi, mkv, webm"
        )
    
    # Generate job ID and save file
    job_id = str(uuid.uuid4())
    filename = file.filename or "unknown"
    file_ext = Path(filename).suffix
    upload_path = settings.UPLOAD_DIR / f"{job_id}{file_ext}"
    
    # Save uploaded file
    async with aiofiles.open(upload_path, "wb") as f:
        content = await file.read()
        await f.write(content)
    
    # Create job entry
    jobs[job_id] = {
        "id": job_id,
        "filename": file.filename,
        "original_path": str(upload_path),
        "status": ProcessingStatus.PENDING,
        "progress": 0,
        "message": "Video uploaded successfully",
        "language": language,
        "aspect_ratio": (aspect_ratio_w, aspect_ratio_h),
        "generate_description": generate_description,
        "description_language": description_language,
        "clips": [],
    }
    
    # Start processing in background
    background_tasks.add_task(process_video_job, job_id)
    
    return VideoJobResponse(
        id=job_id,
        status=ProcessingStatus.PENDING,
        progress=0,
        message="Video uploaded. Processing started.",
        clips_count=0,
    )


@router.post("/youtube", response_model=VideoJobResponse)
async def upload_youtube(
    request: YouTubeUploadRequest,
    background_tasks: BackgroundTasks,
):
    """
    Process a YouTube video (legacy endpoint, use /url for all platforms)
    """
    # Redirect to the new URL endpoint
    url_request = URLUploadRequest(
        url=request.url,
        language=request.language,
        aspect_ratio=request.aspect_ratio,
        generate_description=request.generate_description,
        description_language=request.description_language,
    )
    return await upload_from_url(url_request, background_tasks)


@router.post("/url", response_model=VideoJobResponse)
async def upload_from_url(
    request: URLUploadRequest,
    background_tasks: BackgroundTasks,
):
    """
    Process a video from any supported URL (30+ platforms)
    
    Supports: YouTube, TikTok, Bilibili, Instagram, Twitter, Facebook, 
    Vimeo, Twitch, Reddit, and many more.
    """
    job_id = str(uuid.uuid4())
    filename = f"{job_id}.mp4"
    upload_path = settings.UPLOAD_DIR / filename
    
    # Detect platform
    platform = video_downloader_service.detect_platform(request.url)
    
    # Create job entry
    jobs[job_id] = {
        "id": job_id,
        "filename": filename,
        "original_path": str(upload_path),
        "status": ProcessingStatus.PENDING,
        "progress": 0,
        "message": f"Video from {platform or 'URL'} queued",
        "language": request.language,
        "aspect_ratio": request.aspect_ratio,
        "generate_description": request.generate_description,
        "description_language": request.description_language,
        "generate_summary": request.generate_summary,
        "summary_language": request.summary_language,
        "clips": [],
        "source_url": request.url,
        "platform": platform,
    }
    
    # Start processing in background
    background_tasks.add_task(process_url_job, job_id, request.url)
    
    return VideoJobResponse(
        id=job_id,
        status=ProcessingStatus.PENDING,
        progress=0,
        message=f"Video from {platform or 'URL'} queued for download.",
        clips_count=0,
    )


async def process_url_job(job_id: str, url: str):
    """Background task to download and process video from any URL"""
    job = jobs.get(job_id)
    if not job:
        return
        
    try:
        job["status"] = ProcessingStatus.DOWNLOADING
        platform = job.get("platform", "video")
        job["message"] = f"Downloading {platform} video..."
        job["progress"] = 5
        
        output_path = Path(job["original_path"])
        
        # Download using multi-platform downloader
        def progress_callback(percent: float, message: str):
            job["progress"] = int(5 + percent * 0.1)  # 5-15%
            job["message"] = message
        
        info = video_downloader_service.download_video(
            url=url,
            output_path=output_path,
            progress_callback=progress_callback,
        )
        
        # Update job with video info
        job["message"] = f"Downloaded: {info.get('title', 'Video')}"
        job["title"] = info.get("title")
        job["duration"] = info.get("duration")
        job["thumbnail"] = info.get("thumbnail")
        job["platform"] = info.get("platform")
        job["platform_name"] = info.get("platform_name")
        
        # Update file path if different
        if info.get("downloaded_file"):
            job["original_path"] = info["downloaded_file"]
        
        # Continue with normal processing
        await process_video_job(job_id)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        job["status"] = ProcessingStatus.FAILED
        job["message"] = f"Download failed: {str(e)}"


# Legacy function - redirects to new implementation
async def process_youtube_job(job_id: str, url: str):
    """Background task to download and process YouTube video (legacy)"""
    await process_url_job(job_id, url)



async def process_video_job(job_id: str):
    """Background task to process video"""
    from services import transcription_service, clip_finder_service, description_service, facecam_detector
    
    job = jobs.get(job_id)
    if not job:
        return
    
    try:
        # Step 0: Detect facecam
        job["message"] = "Detecting facecam region..."
        job["progress"] = 5
        
        try:
            facecam_region = facecam_detector.detect_facecam_region(job["original_path"])
            job["facecam_region"] = facecam_region
            if facecam_region:
                job["message"] = f"Facecam detected at {facecam_region.get('is_corner', 'unknown')} corner"
            else:
                job["message"] = "No facecam detected, will use center crop"
        except Exception as e:
            job["facecam_region"] = None
            job["message"] = f"Facecam detection skipped: {str(e)}"
        
        # Step 1: Transcribe
        job["status"] = ProcessingStatus.TRANSCRIBING
        job["progress"] = 10
        job["message"] = "Transcribing video..."
        
        def update_progress(text):
            if job_id in jobs:
                jobs[job_id]["transcript"] = text
                word_count = len(text.split())
                jobs[job_id]["message"] = f"Transcribing... ({word_count} words)"

        transcription = transcription_service.transcribe(
            file_path=job["original_path"],
            language=job["language"],
            progress_callback=update_progress
        )
        job["transcript"] = transcription["text"]
        job["language"] = transcription["language"]
        job["progress"] = 40
        
        # Check if using fallback
        is_fallback = transcription.get("_is_fallback", False)
        if is_fallback:
            job["message"] = "Using fallback transcription (limited mode)"
        
        # Step 1.5: Generate Summary (if requested)
        if job.get("generate_summary", False):
            try:
                from services import summarizer_service
                job["message"] = "Generating AI summary..."
                summary_lang = job.get("summary_language", "en")
                
                summary = summarizer_service.summarize(
                    transcript=transcription["text"],
                    language=summary_lang,
                )
                job["summary"] = summary
                job["message"] = "Summary generated"
            except Exception as e:
                print(f"Summary generation failed: {e}")
                # Don't fail the whole job
        
        # Step 2: Find clips
        job["status"] = ProcessingStatus.FINDING_CLIPS
        job["message"] = "Finding optimal clips..."
        
        # Pass either the ClipsAI object or the full transcription dict for fallback
        transcription_for_clips = transcription.get("_transcription_obj") or transcription
        clips = clip_finder_service.find_clips(
            transcription_obj=transcription_for_clips
        )
        job["clips"] = clips
        job["progress"] = 70
        
        # Step 3: Generate descriptions (optional)
        if job["generate_description"] and clips:
            job["status"] = ProcessingStatus.GENERATING_DESCRIPTION
            job["message"] = "Generating descriptions..."
            
            for clip in job["clips"]:
                try:
                    result = description_service.generate_description(
                        transcript=clip["transcript"],
                        language=job["description_language"],
                    )
                    clip["description"] = result["description"]
                    clip["hashtags"] = result["hashtags"]
                except Exception as e:
                    # Don't fail the whole job if description fails
                    clip["description"] = clip["transcript"][:200] + "..."
                    clip["hashtags"] = ["#video", "#clip"]
            
            job["progress"] = 90
        
        # Complete
        job["status"] = ProcessingStatus.COMPLETED
        job["progress"] = 100
        job["message"] = f"Found {len(clips)} clips!"
        
        if is_fallback:
            job["message"] += " (Fallback mode - install pyannote for full features)"
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        job["status"] = ProcessingStatus.FAILED
        job["message"] = f"Error: {str(e)}"


@router.get("/status/{job_id}", response_model=VideoJobResponse)
async def get_job_status(job_id: str):
    """Get the status of a processing job"""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return VideoJobResponse(
        id=job["id"],
        status=job["status"],
        progress=job["progress"],
        message=job["message"],
        clips_count=len(job.get("clips", [])),
    )


@router.get("/job/{job_id}")
async def get_job_details(job_id: str):
    """Get full job details including clips"""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job


@router.get("/stream/{job_id}")
async def stream_job_progress(job_id: str):
    """
    Server-Sent Events (SSE) stream for real-time job progress
    """
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    async def event_generator():
        last_message = ""
        last_transcript = ""
        
        while True:
            job = jobs.get(job_id)
            if not job:
                yield f"event: error\ndata: {json.dumps({'message': 'Job not found'})}\n\n"
                break
            
            # Send progress updates
            message = job.get("message", "")
            progress = job.get("progress", 0)
            status = job.get("status", "")
            transcript = job.get("transcript", "")
            word_count = len(transcript.split()) if transcript else 0
            
            # Only send if something changed
            if message != last_message or progress > 0:
                event_data = {
                    "stage": status,
                    "percent": progress,
                    "message": message,
                    "transcript": transcript,
                    "word_count": word_count,
                }
                yield f"event: progress\ndata: {json.dumps(event_data)}\n\n"
                last_message = message
            
            # Check if job is complete or failed
            if status == "completed":
                final_data = {
                    "stage": "complete",
                    "percent": 100,
                    "message": job.get("message", "Complete"),
                    "transcript": transcript,
                    "word_count": word_count,
                    "summary": job.get("summary"),
                }
                yield f"event: complete\ndata: {json.dumps(final_data)}\n\n"
                break
            elif status == "failed":
                yield f"event: error\ndata: {json.dumps({'message': job.get('error', 'Unknown error')})}\n\n"
                break
            
            await asyncio.sleep(0.5)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
