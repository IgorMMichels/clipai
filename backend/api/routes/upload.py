"""
Video Upload API Routes
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pathlib import Path
from typing import Optional
import uuid
import shutil
import aiofiles

from config import settings
from models.schemas import VideoUploadRequest, VideoJobResponse, ProcessingStatus

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
    file_ext = Path(file.filename).suffix
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


async def process_video_job(job_id: str):
    """Background task to process video"""
    from services import transcription_service, clip_finder_service, description_service
    
    job = jobs.get(job_id)
    if not job:
        return
    
    try:
        # Step 1: Transcribe
        job["status"] = ProcessingStatus.TRANSCRIBING
        job["progress"] = 10
        job["message"] = "Transcribing video..."
        
        transcription = transcription_service.transcribe(
            file_path=job["original_path"],
            language=job["language"],
        )
        job["transcript"] = transcription["text"]
        job["language"] = transcription["language"]
        job["progress"] = 40
        
        # Check if using fallback
        is_fallback = transcription.get("_is_fallback", False)
        if is_fallback:
            job["message"] = "Using fallback transcription (limited mode)"
        
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
