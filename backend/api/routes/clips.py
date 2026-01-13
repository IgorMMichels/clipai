"""
Clips API Routes
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pathlib import Path
from typing import List, Optional
import uuid

from config import settings
from models.schemas import ClipExportRequest, ProcessingStatus

router = APIRouter(prefix="/clips", tags=["Clips"])

# Reference to jobs storage (shared with upload routes)
from api.routes.upload import jobs

# Export jobs storage
export_jobs = {}


@router.get("/{job_id}")
async def get_clips(job_id: str):
    """Get all clips for a job"""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] != ProcessingStatus.COMPLETED:
        raise HTTPException(
            status_code=400, 
            detail=f"Job not completed. Status: {job['status']}"
        )
    
    return {
        "job_id": job_id,
        "video_filename": job["filename"],
        "language": job["language"],
        "transcript": job.get("transcript", ""),
        "clips": job["clips"],
    }


@router.post("/{job_id}/export")
async def export_clips(
    job_id: str,
    background_tasks: BackgroundTasks,
    request: ClipExportRequest,
):
    """
    Export selected clips with options
    
    - Resize to aspect ratio
    - Add music
    - Burn subtitles
    - Generate descriptions
    """
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] != ProcessingStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed. Status: {job['status']}"
        )
    
    # Create export job
    export_id = str(uuid.uuid4())
    export_jobs[export_id] = {
        "id": export_id,
        "source_job_id": job_id,
        "status": ProcessingStatus.PENDING,
        "progress": 0,
        "message": "Export started",
        "clip_ids": request.clip_ids,
        "options": request.model_dump(),
        "outputs": [],
    }
    
    # Start export in background
    background_tasks.add_task(
        process_export,
        export_id,
        job,
        request,
    )
    
    return {
        "export_id": export_id,
        "status": "started",
        "message": f"Exporting {len(request.clip_ids)} clips",
    }


async def process_export(
    export_id: str,
    job: dict,
    request: ClipExportRequest,
):
    """Background task to export clips"""
    from services import video_editor_service, resize_service, effects_service
    
    export = export_jobs.get(export_id)
    if not export:
        return
    
    try:
        video_path = Path(job["original_path"])
        total_clips = len(request.clip_ids)
        
        for i, clip_id in enumerate(request.clip_ids):
            # Find clip data
            clip = next((c for c in job["clips"] if c["id"] == clip_id), None)
            if not clip:
                continue
            
            export["message"] = f"Processing clip {i+1}/{total_clips}"
            export["progress"] = int((i / total_clips) * 100)
            
            # Create output directory
            output_dir = settings.OUTPUT_DIR / job["id"]
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Step 1: Trim clip
            clip_path = output_dir / f"clip_{i+1}_raw.mp4"
            video_editor_service.trim_clip(
                input_path=video_path,
                output_path=clip_path,
                start_time=clip["start_time"],
                end_time=clip["end_time"],
            )
            
            # Step 2: Resize (if needed)
            if request.aspect_ratio != (16, 9) or request.layout == "stacked":
                resized_path = output_dir / f"clip_{i+1}_resized.mp4"
                
                # Determine AR for face tracking
                face_ar = request.aspect_ratio
                if request.layout == "stacked":
                    face_ar = (1, 1)  # Square crop for face in stacked mode
                    
                crops = resize_service.resize(
                    video_path=clip_path,
                    pyannote_token=settings.HUGGINGFACE_TOKEN,
                    aspect_ratio=face_ar,
                )
                
                if request.layout == "stacked":
                    video_editor_service.apply_stacked_layout(
                        input_path=clip_path,
                        output_path=resized_path,
                        crops_data=crops,
                        fps=60  # Force 60fps for viral
                    )
                else:
                    video_editor_service.resize_video(
                        input_path=clip_path,
                        output_path=resized_path,
                        crops_data=crops,
                        fps=60  # Force 60fps
                    )
                clip_path = resized_path
            
            # Step 3: Add subtitles (if requested)
            if request.add_subtitles:
                subtitled_path = output_dir / f"clip_{i+1}_subtitled.mp4"
                
                # Extract actual subtitles from full transcription
                full_transcription = job.get("transcription", {})
                source_words = full_transcription.get("words", [])
                
                # If no words, fallback to sentences, else fallback to full text
                subtitles = []
                if source_words:
                    # Use words for "live" feel (karaoke style or just fast paced)
                    # Ideally we group words into short phrases (captions)
                    # For now, let's just use words or sentences. 
                    # "Viral" usually means 1-3 words per chunk.
                    # Let's use the words directly? Or better, group them.
                    # For simplicity/robustness, let's use words but maybe checking sentences is safer?
                    # Let's use sentences but cut them if they are too long?
                    # Actually, let's just use the words.
                    
                    for w in source_words:
                        if w["end_time"] > clip["start_time"] and w["start_time"] < clip["end_time"]:
                            sub = {
                                "text": w["text"],
                                "start_time": max(0.0, w["start_time"] - clip["start_time"]),
                                "end_time": min(clip["duration"], w["end_time"] - clip["start_time"])
                            }
                            subtitles.append(sub)
                elif full_transcription.get("sentences"):
                    for s in full_transcription["sentences"]:
                        if s["end_time"] > clip["start_time"] and s["start_time"] < clip["end_time"]:
                            sub = {
                                "text": s["text"],
                                "start_time": max(0.0, s["start_time"] - clip["start_time"]),
                                "end_time": min(clip["duration"], s["end_time"] - clip["start_time"])
                            }
                            subtitles.append(sub)
                else:
                    # Fallback
                    subtitles = [{"text": clip["transcript"], "start_time": 0, "end_time": clip["duration"]}]
                
                video_editor_service.add_subtitles(
                    video_path=clip_path,
                    output_path=subtitled_path,
                    subtitles=subtitles,
                    font_size=50, # Bigger for viral
                    font_color="yellow", # Classic viral color
                    outline_color="black"
                )
                clip_path = subtitled_path
            
            # Step 4: Add music (if requested)
            if request.add_music and request.music_track:
                music_path = settings.BASE_DIR / "assets" / "music" / request.music_track
                if music_path.exists():
                    final_path = output_dir / f"clip_{i+1}_final.mp4"
                    effects_service.add_music(
                        video_path=clip_path,
                        output_path=final_path,
                        music_path=music_path,
                    )
                    clip_path = final_path
            
            # Add to outputs
            export["outputs"].append({
                "clip_id": clip_id,
                "output_path": str(clip_path),
                "description": clip.get("description", ""),
                "hashtags": clip.get("hashtags", []),
            })
        
        export["status"] = ProcessingStatus.COMPLETED
        export["progress"] = 100
        export["message"] = f"Exported {len(export['outputs'])} clips"
        
    except Exception as e:
        export["status"] = ProcessingStatus.FAILED
        export["message"] = f"Export failed: {str(e)}"


@router.get("/export/{export_id}")
async def get_export_status(export_id: str):
    """Get export job status"""
    export = export_jobs.get(export_id)
    if not export:
        raise HTTPException(status_code=404, detail="Export job not found")
    
    return export


@router.get("/download/{export_id}/{clip_index}")
async def download_clip(export_id: str, clip_index: int):
    """Download an exported clip"""
    export = export_jobs.get(export_id)
    if not export:
        raise HTTPException(status_code=404, detail="Export job not found")
    
    if export["status"] != ProcessingStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Export not completed")
    
    if clip_index >= len(export["outputs"]):
        raise HTTPException(status_code=404, detail="Clip not found")
    
    output = export["outputs"][clip_index]
    file_path = Path(output["output_path"])
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="video/mp4",
    )


@router.post("/{job_id}/preview/{clip_id}")
async def generate_preview(
    job_id: str, 
    clip_id: str,
    aspect_ratio_w: int = 9,
    aspect_ratio_h: int = 16,
):
    """Generate a quick preview for a specific clip"""
    from services import video_editor_service
    
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    clip = next((c for c in job["clips"] if c["id"] == clip_id), None)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
        
    # Define output path
    output_dir = settings.OUTPUT_DIR / job_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_filename = f"preview_{clip_id}.mp4"
    output_path = output_dir / output_filename
    
    # Return existing if available
    if output_path.exists():
        return {"url": f"/outputs/{job_id}/{output_filename}", "status": "ready"}
        
    try:
        video_path = Path(job["original_path"])
        video_editor_service.generate_preview(
            input_path=video_path,
            output_path=output_path,
            start_time=clip["start_time"],
            end_time=clip["end_time"],
            aspect_ratio=(aspect_ratio_w, aspect_ratio_h),
        )
        return {"url": f"/outputs/{job_id}/{output_filename}", "status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

