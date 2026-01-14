"""
Transcription API Routes with SSE Real-time Progress
Standalone transcription, summarization, and translation endpoints
Inspired by AI-Video-Transcriber: https://github.com/wendy7756/AI-Video-Transcriber
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from pydantic import BaseModel, HttpUrl
from pathlib import Path
from typing import Optional, List
import uuid
import json
import asyncio
import aiofiles
from datetime import datetime

from config import settings

router = APIRouter(prefix="/transcribe", tags=["Transcription"])

# In-memory job storage
transcription_jobs = {}


class TranscribeURLRequest(BaseModel):
    """Request for transcribing a video from URL"""
    url: str
    language: Optional[str] = None  # Auto-detect if None
    summary_language: str = "en"
    generate_summary: bool = True
    generate_translation: bool = False
    translation_language: Optional[str] = None
    optimize_with_ai: bool = True


class TranscribeResponse(BaseModel):
    """Response for transcription job creation"""
    job_id: str
    status: str
    message: str


class TranscriptionResult(BaseModel):
    """Full transcription result"""
    job_id: str
    status: str
    transcript: Optional[str] = None
    transcript_language: Optional[str] = None
    summary: Optional[dict] = None
    translation: Optional[dict] = None
    segments: Optional[List[dict]] = None
    duration: Optional[float] = None
    platform: Optional[str] = None
    title: Optional[str] = None
    error: Optional[str] = None


@router.post("/url", response_model=TranscribeResponse)
async def transcribe_from_url(
    request: TranscribeURLRequest,
    background_tasks: BackgroundTasks,
):
    """
    Transcribe a video from URL with real-time SSE progress
    
    Supports 30+ platforms including YouTube, TikTok, Bilibili, Instagram, Twitter, etc.
    
    - Returns a job_id to track progress via SSE
    - Use /transcribe/stream/{job_id} for real-time updates
    - Use /transcribe/result/{job_id} for final result
    """
    job_id = str(uuid.uuid4())
    
    # Create job entry
    transcription_jobs[job_id] = {
        "id": job_id,
        "status": "pending",
        "progress": 0,
        "message": "Job created",
        "url": request.url,
        "language": request.language,
        "summary_language": request.summary_language,
        "generate_summary": request.generate_summary,
        "generate_translation": request.generate_translation,
        "translation_language": request.translation_language,
        "optimize_with_ai": request.optimize_with_ai,
        "created_at": datetime.utcnow().isoformat(),
        "events": [],
    }
    
    # Start processing in background
    background_tasks.add_task(process_transcription_job, job_id)
    
    return TranscribeResponse(
        job_id=job_id,
        status="pending",
        message="Transcription job created. Use /transcribe/stream/{job_id} for real-time updates.",
    )


@router.post("/file", response_model=TranscribeResponse)
async def transcribe_from_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    language: Optional[str] = None,
    summary_language: str = "en",
    generate_summary: bool = True,
    generate_translation: bool = False,
    translation_language: Optional[str] = None,
    optimize_with_ai: bool = True,
):
    """
    Transcribe an uploaded video/audio file
    
    Accepts: mp4, mov, avi, mkv, webm, mp3, wav, m4a, flac
    """
    # Validate file type
    allowed_types = [
        "video/mp4", "video/quicktime", "video/x-msvideo", "video/x-matroska", "video/webm",
        "audio/mpeg", "audio/wav", "audio/x-m4a", "audio/flac", "audio/mp3",
    ]
    
    # Also check by extension
    allowed_extensions = [".mp4", ".mov", ".avi", ".mkv", ".webm", ".mp3", ".wav", ".m4a", ".flac"]
    ext = Path(file.filename or "").suffix.lower()
    
    if file.content_type not in allowed_types and ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: video (mp4, mov, avi, mkv, webm) and audio (mp3, wav, m4a, flac)"
        )
    
    # Generate job ID and save file
    job_id = str(uuid.uuid4())
    filename = file.filename or f"upload{ext}"
    file_ext = Path(filename).suffix or ext
    upload_path = settings.UPLOAD_DIR / f"{job_id}{file_ext}"
    
    # Save uploaded file
    async with aiofiles.open(upload_path, "wb") as f:
        content = await file.read()
        await f.write(content)
    
    # Create job entry
    transcription_jobs[job_id] = {
        "id": job_id,
        "status": "pending",
        "progress": 0,
        "message": "File uploaded",
        "file_path": str(upload_path),
        "filename": filename,
        "language": language,
        "summary_language": summary_language,
        "generate_summary": generate_summary,
        "generate_translation": generate_translation,
        "translation_language": translation_language,
        "optimize_with_ai": optimize_with_ai,
        "created_at": datetime.utcnow().isoformat(),
        "events": [],
    }
    
    # Start processing in background
    background_tasks.add_task(process_transcription_job, job_id)
    
    return TranscribeResponse(
        job_id=job_id,
        status="pending",
        message="File uploaded. Processing started.",
    )


@router.get("/stream/{job_id}")
async def stream_progress(job_id: str):
    """
    Server-Sent Events (SSE) stream for real-time progress updates
    
    Event types:
    - progress: {stage, percent, message}
    - transcript: {text} (partial transcript updates)
    - complete: {result}
    - error: {message}
    """
    job = transcription_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    async def event_generator():
        last_event_count = 0
        
        while True:
            job = transcription_jobs.get(job_id)
            if not job:
                yield f"event: error\ndata: {json.dumps({'message': 'Job not found'})}\n\n"
                break
            
            # Send any new events
            events = job.get("events", [])
            while last_event_count < len(events):
                event = events[last_event_count]
                yield f"event: {event['type']}\ndata: {json.dumps(event['data'])}\n\n"
                last_event_count += 1
            
            # Check if job is complete or failed
            if job["status"] in ["completed", "failed"]:
                if job["status"] == "completed":
                    result = {
                        "job_id": job_id,
                        "status": "completed",
                        "transcript": job.get("transcript"),
                        "transcript_language": job.get("transcript_language"),
                        "summary": job.get("summary"),
                        "translation": job.get("translation"),
                        "duration": job.get("duration"),
                        "title": job.get("title"),
                    }
                    yield f"event: complete\ndata: {json.dumps(result)}\n\n"
                else:
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


@router.get("/result/{job_id}")
async def get_result(job_id: str):
    """Get the final transcription result"""
    job = transcription_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "message": job["message"],
        "transcript": job.get("transcript"),
        "transcript_language": job.get("transcript_language"),
        "transcript_language_name": job.get("transcript_language_name"),
        "summary": job.get("summary"),
        "translation": job.get("translation"),
        "segments": job.get("segments"),
        "duration": job.get("duration"),
        "platform": job.get("platform"),
        "title": job.get("title"),
        "error": job.get("error"),
        "created_at": job.get("created_at"),
    }


@router.get("/status/{job_id}")
async def get_status(job_id: str):
    """Get job status (lightweight endpoint)"""
    job = transcription_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "message": job["message"],
    }


@router.get("/export/{job_id}")
async def export_markdown(
    job_id: str,
    include_transcript: bool = True,
    include_summary: bool = True,
    include_translation: bool = True,
):
    """
    Export transcription result as Markdown file
    """
    job = transcription_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    from services.exporter import export_to_markdown
    
    markdown_content = export_to_markdown(
        transcript=job.get("transcript") if include_transcript else None,
        summary=job.get("summary") if include_summary else None,
        translation=job.get("translation") if include_translation else None,
        title=job.get("title", "Transcription"),
        language=job.get("transcript_language"),
        platform=job.get("platform"),
        duration=job.get("duration"),
    )
    
    # Save to temp file and return
    export_path = settings.OUTPUT_DIR / f"transcription_{job_id}.md"
    async with aiofiles.open(export_path, "w", encoding="utf-8") as f:
        await f.write(markdown_content)
    
    return FileResponse(
        path=export_path,
        filename=f"transcription_{job_id}.md",
        media_type="text/markdown",
    )


@router.get("/languages")
async def get_supported_languages():
    """Get list of supported languages for transcription and summarization"""
    from services.summarizer import SUMMARY_LANGUAGES
    from services.translator import SUPPORTED_LANGUAGES
    
    return {
        "transcription_languages": [
            {"code": "auto", "name": "Auto-detect"},
            {"code": "en", "name": "English"},
            {"code": "zh", "name": "Chinese"},
            {"code": "es", "name": "Spanish"},
            {"code": "fr", "name": "French"},
            {"code": "de", "name": "German"},
            {"code": "it", "name": "Italian"},
            {"code": "pt", "name": "Portuguese"},
            {"code": "ru", "name": "Russian"},
            {"code": "ja", "name": "Japanese"},
            {"code": "ko", "name": "Korean"},
            {"code": "ar", "name": "Arabic"},
            {"code": "hi", "name": "Hindi"},
        ],
        "summary_languages": [
            {"code": code, "name": name}
            for code, name in SUMMARY_LANGUAGES.items()
        ],
        "translation_languages": [
            {"code": code, "name": name}
            for code, name in SUPPORTED_LANGUAGES.items()
        ],
    }


@router.get("/platforms")
async def get_supported_platforms():
    """Get list of supported video platforms"""
    from services.video_downloader import video_downloader_service
    
    return {
        "platforms": video_downloader_service.get_supported_platforms()
    }


async def process_transcription_job(job_id: str):
    """Background task to process transcription"""
    from services.transcriber import transcription_service
    from services.summarizer import summarizer_service, SUMMARY_LANGUAGES
    from services.translator import translator_service, SUPPORTED_LANGUAGES
    from services.video_downloader import video_downloader_service
    
    job = transcription_jobs.get(job_id)
    if not job:
        return
    
    def add_event(event_type: str, data: dict):
        job["events"].append({"type": event_type, "data": data})
    
    try:
        file_path = job.get("file_path")
        
        # Step 1: Download if URL provided
        if "url" in job and not file_path:
            job["status"] = "downloading"
            job["progress"] = 5
            job["message"] = "Downloading video..."
            add_event("progress", {"stage": "download", "percent": 5, "message": "Starting download..."})
            
            url = job["url"]
            output_path = settings.UPLOAD_DIR / f"{job_id}.mp4"
            
            def download_progress(percent: float, message: str):
                job["progress"] = int(5 + percent * 0.15)  # 5-20%
                job["message"] = message
                add_event("progress", {"stage": "download", "percent": percent, "message": message})
            
            try:
                info = video_downloader_service.download_video(
                    url=url,
                    output_path=output_path,
                    progress_callback=download_progress,
                )
                
                file_path = info.get("downloaded_file", str(output_path))
                job["file_path"] = file_path
                job["title"] = info.get("title")
                job["duration"] = info.get("duration")
                job["platform"] = info.get("platform")
                job["platform_name"] = info.get("platform_name")
                
                add_event("progress", {"stage": "download", "percent": 100, "message": f"Downloaded: {info.get('title', 'Video')}"})
                
            except Exception as e:
                raise Exception(f"Download failed: {str(e)}")
        
        # Step 2: Transcribe
        job["status"] = "transcribing"
        job["progress"] = 25
        job["message"] = "Transcribing audio..."
        add_event("progress", {"stage": "transcribe", "percent": 0, "message": "Starting transcription..."})
        
        transcript_text = ""
        
        def transcribe_progress(text: str):
            nonlocal transcript_text
            transcript_text = text
            word_count = len(text.split())
            job["progress"] = min(60, 25 + word_count // 50)  # Progress based on word count
            job["message"] = f"Transcribing... ({word_count} words)"
            # Send partial transcript updates
            add_event("transcript", {"text": text, "word_count": word_count})
        
        result = transcription_service.transcribe(
            file_path=file_path,
            language=job.get("language"),
            progress_callback=transcribe_progress,
            optimize_with_ai=job.get("optimize_with_ai", True),
        )
        
        job["transcript"] = result["text"]
        job["transcript_language"] = result.get("language", "en")
        job["transcript_language_name"] = SUPPORTED_LANGUAGES.get(result.get("language", "en"), "English")
        job["segments"] = result.get("sentences", [])
        
        if not job.get("duration"):
            job["duration"] = result.get("end_time", 0)
        
        add_event("progress", {"stage": "transcribe", "percent": 100, "message": "Transcription complete"})
        job["progress"] = 65
        
        # Step 3: Generate Summary (optional)
        if job.get("generate_summary") and result["text"]:
            job["status"] = "summarizing"
            job["message"] = "Generating summary..."
            add_event("progress", {"stage": "summarize", "percent": 0, "message": "Generating AI summary..."})
            
            summary_lang = job.get("summary_language", "en")
            summary = summarizer_service.summarize(
                transcript=result["text"],
                language=summary_lang,
                style="comprehensive",
            )
            job["summary"] = summary
            job["progress"] = 80
            
            add_event("progress", {"stage": "summarize", "percent": 100, "message": "Summary generated"})
        
        # Step 4: Translate (optional, when summary language differs from transcript language)
        if job.get("generate_translation"):
            translation_lang = job.get("translation_language")
            transcript_lang = result.get("language", "en")
            
            # Auto-set translation language if not specified
            if not translation_lang:
                # Translate to summary language if different from transcript
                if job.get("summary_language") != transcript_lang:
                    translation_lang = job.get("summary_language", "en")
            
            if translation_lang and translation_lang != transcript_lang:
                job["status"] = "translating"
                job["message"] = f"Translating to {SUPPORTED_LANGUAGES.get(translation_lang, translation_lang)}..."
                add_event("progress", {"stage": "translate", "percent": 0, "message": "Translating transcript..."})
                
                translation = translator_service.translate(
                    text=result["text"],
                    target_language=translation_lang,
                    source_language=transcript_lang,
                )
                job["translation"] = translation
                job["progress"] = 95
                
                add_event("progress", {"stage": "translate", "percent": 100, "message": "Translation complete"})
        
        # Complete
        job["status"] = "completed"
        job["progress"] = 100
        job["message"] = "Processing complete!"
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        job["status"] = "failed"
        job["error"] = str(e)
        job["message"] = f"Error: {str(e)}"
        add_event("error", {"message": str(e)})
