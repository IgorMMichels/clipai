"""
Clips API Routes
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pathlib import Path
from typing import List, Optional
import uuid
import subprocess
import time
import os
import json
from datetime import datetime, timedelta

from config import settings
from models.schemas import ClipExportRequest, ProcessingStatus

router = APIRouter(prefix="/clips", tags=["Clips"])

# Reference to jobs storage (shared with upload routes)
from api.routes.upload import jobs

# Export jobs storage
export_jobs = {}

# Local DB path for persistence
DB_PATH = settings.BASE_DIR / "data" / "clipai.json"


def load_db():
    """Load local database"""
    if DB_PATH.exists():
        try:
            with open(DB_PATH, "r") as f:
                return json.load(f)
        except:
            pass
    return {"exports": {}, "created_at": {}}


def save_db(data):
    """Save local database"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2, default=str)


def cleanup_old_files():
    """Remove files older than 1 week"""
    one_week_ago = datetime.now() - timedelta(days=7)
    cleaned_count = 0
    
    # Clean outputs directory
    if settings.OUTPUT_DIR.exists():
        for job_dir in settings.OUTPUT_DIR.iterdir():
            if job_dir.is_dir():
                try:
                    # Check modification time
                    mtime = datetime.fromtimestamp(job_dir.stat().st_mtime)
                    if mtime < one_week_ago:
                        # Remove entire directory
                        import shutil
                        shutil.rmtree(job_dir)
                        cleaned_count += 1
                except Exception as e:
                    print(f"Error cleaning {job_dir}: {e}")
    
    # Clean uploads directory
    if settings.UPLOAD_DIR.exists():
        for file in settings.UPLOAD_DIR.iterdir():
            try:
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                if mtime < one_week_ago:
                    if file.is_file():
                        file.unlink()
                    elif file.is_dir():
                        import shutil
                        shutil.rmtree(file)
                    cleaned_count += 1
            except Exception as e:
                print(f"Error cleaning {file}: {e}")
    
    return cleaned_count


@router.post("/cleanup")
async def run_cleanup():
    """Manually trigger cleanup of old files"""
    cleaned = cleanup_old_files()
    return {"message": f"Cleaned up {cleaned} old files/directories"}


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


@router.post("/{job_id}/export/{clip_id}")
async def export_single_clip(
    job_id: str,
    clip_id: str,
    background_tasks: BackgroundTasks,
):
    """Export a single clip with high quality settings"""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] != ProcessingStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed. Status: {job['status']}"
        )
    
    clip = next((c for c in job["clips"] if c["id"] == clip_id), None)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    
    # Create export job
    export_id = str(uuid.uuid4())
    export_jobs[export_id] = {
        "id": export_id,
        "source_job_id": job_id,
        "clip_id": clip_id,
        "status": ProcessingStatus.PROCESSING,
        "progress": 0,
        "progress_message": "Starting export...",
        "output_path": None,
        "started_at": time.time(),
    }
    
    # Start export in background
    background_tasks.add_task(
        process_single_export,
        export_id,
        job,
        clip,
    )
    
    return {
        "export_id": export_id,
        "status": "started",
        "message": f"Exporting clip",
    }


async def process_single_export(export_id: str, job: dict, clip: dict):
    """Background task to export a single clip with high quality"""
    from services import video_editor_service
    
    export = export_jobs.get(export_id)
    if not export:
        return
    
    try:
        video_path = Path(job["original_path"])
        output_dir = settings.OUTPUT_DIR / job["id"]
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Final output path
        safe_name = f"clip_{clip['id'][:8]}_export.mp4"
        output_path = output_dir / safe_name
        
        export["progress"] = 10
        export["progress_message"] = "Trimming video..."
        
        # Get facecam and subtitles
        facecam_region = job.get("facecam_region")
        transcription = job.get("transcription", {})
        words = transcription.get("words", [])
        
        # Build subtitles
        subtitles = []
        if words:
            for w in words:
                if w["end_time"] > clip["start_time"] and w["start_time"] < clip["end_time"]:
                    subtitles.append({
                        "text": w["text"],
                        "start_time": w["start_time"],
                        "end_time": w["end_time"]
                    })
        else:
            subtitles = [{
                "text": clip.get("transcript", ""),
                "start_time": clip["start_time"],
                "end_time": clip["end_time"]
            }]
        
        export["progress"] = 30
        export["progress_message"] = "Applying effects..."
        
        # Use high quality export with PiP if available
        if facecam_region:
            export["progress_message"] = "Processing with PiP layout..."
            video_editor_service.process_viral_clip_with_pip(
                input_path=video_path,
                output_path=output_path,
                start_time=clip["start_time"],
                end_time=clip["end_time"],
                facecam_region=facecam_region,
                subtitles=subtitles,
                pip_position=facecam_region.get("is_corner", "bottom-right"),
                pip_scale=0.3,
                fps=60  # High quality 60fps
            )
        else:
            export["progress_message"] = "Rendering high quality video..."
            # Simple high quality export
            video_editor_service.generate_preview(
                input_path=video_path,
                output_path=output_path,
                start_time=clip["start_time"],
                end_time=clip["end_time"],
                aspect_ratio=(9, 16),
                subtitles=subtitles,
            )
        
        export["progress"] = 100
        export["progress_message"] = "Export complete!"
        export["status"] = ProcessingStatus.COMPLETED
        export["output_path"] = str(output_path)
        export["download_url"] = f"/outputs/{job['id']}/{safe_name}"
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        export["status"] = ProcessingStatus.FAILED
        export["progress_message"] = f"Export failed: {str(e)}"


@router.get("/export/{export_id}/status")
async def get_export_status(export_id: str):
    """Get export job status with progress"""
    export = export_jobs.get(export_id)
    if not export:
        raise HTTPException(status_code=404, detail="Export job not found")
    
    return {
        "id": export["id"],
        "status": export["status"],
        "progress": export["progress"],
        "message": export["progress_message"],
        "output_path": export.get("output_path"),
        "download_url": export.get("download_url"),
    }


@router.get("/export/{export_id}/download")
async def download_exported_clip(export_id: str):
    """Download an exported clip"""
    export = export_jobs.get(export_id)
    if not export:
        raise HTTPException(status_code=404, detail="Export job not found")
    
    if export["status"] != ProcessingStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Export not completed")
    
    file_path = Path(export["output_path"])
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=f"clip_export_{export_id[:8]}.mp4",
        media_type="video/mp4",
    )


@router.post("/{job_id}/export")
async def export_clips(
    job_id: str,
    background_tasks: BackgroundTasks,
    request: ClipExportRequest,
):
    """
    Export selected clips with options (legacy endpoint)
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
        "progress_message": "Export started",
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
            
            export["progress_message"] = f"Processing clip {i+1}/{total_clips}"
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
                
                subtitles = []
                if source_words:
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
                    font_size=50,
                    font_color="yellow",
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
        export["progress_message"] = f"Exported {len(export['outputs'])} clips"
        
    except Exception as e:
        export["status"] = ProcessingStatus.FAILED
        export["progress_message"] = f"Export failed: {str(e)}"


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


@router.get("/{job_id}/thumbnail/{clip_id}")
async def get_thumbnail(job_id: str, clip_id: str):
    """Generate and return a thumbnail for a specific clip"""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    clip = next((c for c in job["clips"] if c["id"] == clip_id), None)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    
    # Define output path
    output_dir = settings.OUTPUT_DIR / job_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    thumbnail_path = output_dir / f"thumb_{clip_id}.jpg"
    
    # Return existing if available
    if thumbnail_path.exists():
        return FileResponse(thumbnail_path, media_type="image/jpeg")
    
    try:
        video_path = Path(job["original_path"])
        
        if not video_path.exists():
            raise HTTPException(status_code=404, detail="Source video not found")
        
        # Extract frame from clip midpoint
        midpoint = clip["start_time"] + (clip["duration"] / 2)
        
        # Simpler FFmpeg command - just extract frame and scale
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(midpoint),
            "-i", str(video_path),
            "-vframes", "1",
            "-vf", "scale=360:-1",  # Scale width to 360, auto height
            "-q:v", "3",
            str(thumbnail_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        
        if thumbnail_path.exists():
            return FileResponse(thumbnail_path, media_type="image/jpeg")
        else:
            # Log the error
            print(f"FFmpeg stderr: {result.stderr.decode()}")
            raise HTTPException(status_code=500, detail="Failed to generate thumbnail")
            
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Thumbnail generation timed out")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{job_id}/preview/{clip_id}")
async def generate_preview(
    job_id: str, 
    clip_id: str,
    aspect_ratio_w: int = 9,
    aspect_ratio_h: int = 16,
    with_subtitles: bool = True,
    with_pip: bool = True,
):
    """Generate a quick preview for a specific clip with PiP and subtitles"""
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
    
    # Include options in filename for caching
    opts = f"{'pip' if with_pip else 'nopip'}_{'sub' if with_subtitles else 'nosub'}"
    output_filename = f"preview_{clip_id}_{opts}.mp4"
    output_path = output_dir / output_filename
    
    # Return existing if available
    if output_path.exists():
        return {"url": f"/outputs/{job_id}/{output_filename}", "status": "ready"}
        
    try:
        video_path = Path(job["original_path"])
        facecam_region = job.get("facecam_region")
        
        # Build subtitles from transcription words
        subtitles = []
        if with_subtitles:
            transcription = job.get("transcription", {})
            words = transcription.get("words", [])
            
            if words:
                for w in words:
                    if w["end_time"] > clip["start_time"] and w["start_time"] < clip["end_time"]:
                        subtitles.append({
                            "text": w["text"],
                            "start_time": w["start_time"],
                            "end_time": w["end_time"]
                        })
            else:
                # Fallback: use clip transcript as single subtitle
                subtitles = [{
                    "text": clip.get("transcript", ""),
                    "start_time": clip["start_time"],
                    "end_time": clip["end_time"]
                }]
        
        # Use the new PiP processing if facecam detected and PiP requested
        if with_pip and facecam_region:
            video_editor_service.process_viral_clip_with_pip(
                input_path=video_path,
                output_path=output_path,
                start_time=clip["start_time"],
                end_time=clip["end_time"],
                facecam_region=facecam_region,
                subtitles=subtitles,
                pip_position=facecam_region.get("is_corner", "bottom-right"),
                pip_scale=0.3,
                fps=30  # Lower fps for preview
            )
        else:
            # Standard preview without PiP
            video_editor_service.generate_preview(
                input_path=video_path,
                output_path=output_path,
                start_time=clip["start_time"],
                end_time=clip["end_time"],
                aspect_ratio=(aspect_ratio_w, aspect_ratio_h),
                subtitles=subtitles if with_subtitles else None,
            )
        
        return {"url": f"/outputs/{job_id}/{output_filename}", "status": "ready"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# Run cleanup on module load (optional - once per server start)
try:
    cleaned = cleanup_old_files()
    if cleaned > 0:
        print(f"[Startup] Cleaned up {cleaned} old files/directories")
except Exception as e:
    print(f"[Startup] Cleanup error: {e}")
