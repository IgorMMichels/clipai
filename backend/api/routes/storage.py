"""
Storage Management API Routes
Allows viewing and deleting uploaded files and outputs
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
from typing import List
import os
import shutil
from datetime import datetime

from config import settings

router = APIRouter(prefix="/storage", tags=["Storage"])


def get_file_size_mb(path: Path) -> float:
    """Get file size in MB"""
    if path.is_file():
        return path.stat().st_size / (1024 * 1024)
    elif path.is_dir():
        total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
        return total / (1024 * 1024)
    return 0


def get_file_info(path: Path) -> dict:
    """Get file/folder info"""
    stat = path.stat()
    return {
        "name": path.name,
        "path": str(path),
        "size_mb": round(get_file_size_mb(path), 2),
        "is_dir": path.is_dir(),
        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
    }


@router.get("/uploads")
async def list_uploads():
    """List all uploaded files"""
    uploads = []
    total_size = 0
    
    if settings.UPLOAD_DIR.exists():
        for item in sorted(settings.UPLOAD_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            info = get_file_info(item)
            uploads.append(info)
            total_size += info["size_mb"]
    
    return {
        "uploads": uploads,
        "total_size_mb": round(total_size, 2),
        "upload_dir": str(settings.UPLOAD_DIR),
    }


@router.get("/outputs")
async def list_outputs():
    """List all output folders"""
    outputs = []
    total_size = 0
    
    if settings.OUTPUT_DIR.exists():
        for item in sorted(settings.OUTPUT_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            info = get_file_info(item)
            # Count files in folder
            if item.is_dir():
                info["file_count"] = len(list(item.rglob("*")))
            outputs.append(info)
            total_size += info["size_mb"]
    
    return {
        "outputs": outputs,
        "total_size_mb": round(total_size, 2),
        "output_dir": str(settings.OUTPUT_DIR),
    }


@router.get("/summary")
async def storage_summary():
    """Get storage summary"""
    upload_size = get_file_size_mb(settings.UPLOAD_DIR) if settings.UPLOAD_DIR.exists() else 0
    output_size = get_file_size_mb(settings.OUTPUT_DIR) if settings.OUTPUT_DIR.exists() else 0
    
    upload_count = len(list(settings.UPLOAD_DIR.iterdir())) if settings.UPLOAD_DIR.exists() else 0
    output_count = len(list(settings.OUTPUT_DIR.iterdir())) if settings.OUTPUT_DIR.exists() else 0
    
    return {
        "uploads": {
            "count": upload_count,
            "size_mb": round(upload_size, 2),
            "path": str(settings.UPLOAD_DIR),
        },
        "outputs": {
            "count": output_count,
            "size_mb": round(output_size, 2),
            "path": str(settings.OUTPUT_DIR),
        },
        "total_size_mb": round(upload_size + output_size, 2),
    }


@router.delete("/uploads/{filename}")
async def delete_upload(filename: str):
    """Delete an uploaded file"""
    file_path = settings.UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Security: ensure path is within upload dir
    if not file_path.resolve().is_relative_to(settings.UPLOAD_DIR.resolve()):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        if file_path.is_dir():
            shutil.rmtree(file_path)
        else:
            file_path.unlink()
        
        return {"message": f"Deleted {filename}", "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/outputs/{folder_name}")
async def delete_output(folder_name: str):
    """Delete an output folder"""
    folder_path = settings.OUTPUT_DIR / folder_name
    
    if not folder_path.exists():
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # Security: ensure path is within output dir
    if not folder_path.resolve().is_relative_to(settings.OUTPUT_DIR.resolve()):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        if folder_path.is_dir():
            shutil.rmtree(folder_path)
        else:
            folder_path.unlink()
        
        return {"message": f"Deleted {folder_name}", "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear/uploads")
async def clear_all_uploads():
    """Delete all uploaded files"""
    try:
        count = 0
        size = 0
        
        if settings.UPLOAD_DIR.exists():
            for item in settings.UPLOAD_DIR.iterdir():
                size += get_file_size_mb(item)
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
                count += 1
        
        return {
            "message": f"Deleted {count} items",
            "freed_mb": round(size, 2),
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear/outputs")
async def clear_all_outputs():
    """Delete all output files"""
    try:
        count = 0
        size = 0
        
        if settings.OUTPUT_DIR.exists():
            for item in settings.OUTPUT_DIR.iterdir():
                size += get_file_size_mb(item)
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
                count += 1
        
        return {
            "message": f"Deleted {count} items",
            "freed_mb": round(size, 2),
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear/all")
async def clear_all_storage():
    """Delete all uploads and outputs"""
    uploads_result = await clear_all_uploads()
    outputs_result = await clear_all_outputs()
    
    return {
        "message": "Cleared all storage",
        "uploads_deleted": uploads_result["message"],
        "outputs_deleted": outputs_result["message"],
        "total_freed_mb": round(uploads_result["freed_mb"] + outputs_result["freed_mb"], 2),
        "success": True
    }
