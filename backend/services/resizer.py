"""
Resizing Service
Handles video aspect ratio conversion with speaker tracking using OpenCV Haar Cascades.
"""
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict
import cv2
import numpy as np

logger = logging.getLogger(__name__)

class ResizeService:
    """Service for resizing videos to different aspect ratios"""
    
    def __init__(self, pyannote_token: Optional[str] = None):
        self.pyannote_token = pyannote_token
    
    @property
    def is_available(self) -> bool:
        return True
    
    def resize(
        self,
        video_path: str | Path,
        pyannote_token: Optional[str] = None,
        aspect_ratio: Tuple[int, int] = (9, 16),
        min_segment_duration: float = 1.5,
        samples_per_segment: int = 13,
    ) -> dict:
        """
        Resize a video to a new aspect ratio with face tracking using OpenCV
        """
        video_path = Path(video_path)
        logger.info(f"Resizing video to {aspect_ratio[0]}:{aspect_ratio[1]} using OpenCV")
        
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video: {video_path}")
            
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        target_w_ratio, target_h_ratio = aspect_ratio
        target_aspect = target_w_ratio / target_h_ratio
        
        # Calculate target crop size
        if width / height > target_aspect:
            # Video is wider than target
            crop_h = height
            crop_w = int(height * target_aspect)
        else:
            # Video is taller than target
            crop_w = width
            crop_h = int(width / target_aspect)
            
        # Detect faces using Haar Cascades
        try:
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        except AttributeError:
            # Fallback if cv2.data is not available (rare)
            logger.warning("cv2.data.haarcascades not found, using center crop")
            return self._center_crop_fallback(video_path, aspect_ratio)

        centers = []
        
        # Sample frames (every 0.5 seconds)
        step_frames = int(fps * 0.5) if fps > 0 else 15
        if step_frames < 1: step_frames = 1
        
        for i in range(0, total_frames, step_frames):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            success, image = cap.read()
            if not success:
                break
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            center_x = width // 2
            
            if len(faces) > 0:
                # Find largest face
                max_area = 0
                for (x, y, w, h) in faces:
                    area = w * h
                    if area > max_area:
                        max_area = area
                        # Center of the face
                        face_x = x + w // 2
                        center_x = face_x
            
            centers.append((i / fps, center_x))
                
        cap.release()
        
        # Segments logic
        segments = []
        if not centers:
             return self._center_crop_fallback(video_path, aspect_ratio)

        current_x = centers[0][1]
        start_t = 0.0
        
        def clamp_x(x):
            half_w = crop_w // 2
            return max(0, min(width - crop_w, x - half_w))

        last_x = current_x
        segment_start_time = 0.0
        
        for t, x in centers:
            # If face moves more than 10% of width, cut
            if abs(x - last_x) > width * 0.1:
                segments.append({
                    "x": clamp_x(last_x),
                    "y": 0,
                    "start_time": segment_start_time,
                    "end_time": t
                })
                segment_start_time = t
                last_x = x
        
        # Add final segment
        segments.append({
            "x": clamp_x(last_x),
            "y": 0,
            "start_time": segment_start_time,
            "end_time": duration
        })
        
        return {
            "crop_width": crop_w,
            "crop_height": crop_h,
            "original_width": width,
            "original_height": height,
            "segments": segments,
            "_crops_obj": None 
        }

    def _center_crop_fallback(self, video_path: Path, aspect_ratio: Tuple[int, int]) -> dict:
        """Fallback center crop"""
        cap = cv2.VideoCapture(str(video_path))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        
        target_w, target_h = aspect_ratio
        target_ratio = target_w / target_h
        
        if width / height > target_ratio:
            crop_h = height
            crop_w = int(height * target_ratio)
        else:
            crop_w = width
            crop_h = int(width / target_ratio)
            
        x = (width - crop_w) // 2
        y = (height - crop_h) // 2
        
        return {
            "crop_width": crop_w,
            "crop_height": crop_h,
            "original_width": width,
            "original_height": height,
            "segments": [{
                "x": x, "y": y, 
                "start_time": 0, 
                "end_time": total_frames/fps if fps else 0
            }],
            "_crops_obj": None
        }

# Singleton instance
resize_service = ResizeService()
