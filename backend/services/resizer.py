"""
ClipsAI Resizing Service
Handles video aspect ratio conversion with speaker tracking
"""
import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Check if clipsai resize is available (requires mediapipe)
RESIZE_AVAILABLE = False
try:
    from clipsai import resize as clipsai_resize
    RESIZE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ClipsAI resize not available: {e}. Speaker tracking disabled.")


class ResizeService:
    """Service for resizing videos to different aspect ratios"""
    
    def __init__(self, pyannote_token: Optional[str] = None):
        self.pyannote_token = pyannote_token
    
    @property
    def is_available(self) -> bool:
        """Check if resize functionality is available"""
        return RESIZE_AVAILABLE
    
    def resize(
        self,
        video_path: str | Path,
        pyannote_token: Optional[str] = None,
        aspect_ratio: Tuple[int, int] = (9, 16),
        min_segment_duration: float = 1.5,
        samples_per_segment: int = 13,
    ) -> dict:
        """
        Resize a video to a new aspect ratio with speaker tracking
        
        Args:
            video_path: Path to the video file
            pyannote_token: HuggingFace token for Pyannote
            aspect_ratio: Target aspect ratio (width, height)
            min_segment_duration: Minimum speaker segment duration
            samples_per_segment: Samples per segment for face detection
        
        Returns:
            dict with crop information and segments
        """
        video_path = Path(video_path)
        
        if not RESIZE_AVAILABLE:
            # Fallback: center crop without speaker tracking
            logger.warning("Using center crop fallback (mediapipe not available)")
            return self._center_crop_fallback(video_path, aspect_ratio)
        
        token = pyannote_token or self.pyannote_token
        
        if not token:
            logger.warning("No Pyannote token provided, using center crop fallback")
            return self._center_crop_fallback(video_path, aspect_ratio)
        
        logger.info(f"Resizing video to {aspect_ratio[0]}:{aspect_ratio[1]}")
        
        crops = clipsai_resize(
            video_file_path=str(video_path.absolute()),
            pyannote_auth_token=token,
            aspect_ratio=aspect_ratio,
            min_segment_duration=min_segment_duration,
            samples_per_segment=samples_per_segment,
        )
        
        logger.info(f"Resize complete. {len(crops.segments)} segments found")
        
        return {
            "crop_width": crops.crop_width,
            "crop_height": crops.crop_height,
            "original_width": crops.original_width,
            "original_height": crops.original_height,
            "segments": [
                {
                    "x": seg.x,
                    "y": seg.y,
                    "start_time": seg.start_time,
                    "end_time": seg.end_time,
                    "speakers": seg.speakers,
                }
                for seg in crops.segments
            ],
            "_crops_obj": crops  # Keep original for MediaEditor
        }
    
    def _center_crop_fallback(
        self, 
        video_path: Path, 
        aspect_ratio: Tuple[int, int]
    ) -> dict:
        """
        Fallback center crop when speaker tracking is not available
        """
        import subprocess
        import json
        
        # Get video dimensions using ffprobe
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "quiet", "-print_format", "json",
                    "-show_streams", str(video_path)
                ],
                capture_output=True,
                text=True
            )
            probe = json.loads(result.stdout)
            video_stream = next(
                (s for s in probe["streams"] if s["codec_type"] == "video"),
                None
            )
            
            if video_stream:
                orig_width = int(video_stream["width"])
                orig_height = int(video_stream["height"])
            else:
                orig_width, orig_height = 1920, 1080
        except Exception as e:
            logger.warning(f"Could not get video dimensions: {e}")
            orig_width, orig_height = 1920, 1080
        
        # Calculate crop dimensions
        target_w, target_h = aspect_ratio
        target_ratio = target_w / target_h
        orig_ratio = orig_width / orig_height
        
        if orig_ratio > target_ratio:
            # Video is wider, crop width
            crop_height = orig_height
            crop_width = int(orig_height * target_ratio)
        else:
            # Video is taller, crop height
            crop_width = orig_width
            crop_height = int(orig_width / target_ratio)
        
        # Center crop position
        x = (orig_width - crop_width) // 2
        y = (orig_height - crop_height) // 2
        
        return {
            "crop_width": crop_width,
            "crop_height": crop_height,
            "original_width": orig_width,
            "original_height": orig_height,
            "segments": [
                {
                    "x": x,
                    "y": y,
                    "start_time": 0,
                    "end_time": None,  # Full video
                    "speakers": [],
                }
            ],
            "_crops_obj": None,
            "_is_fallback": True,
        }


# Singleton instance
resize_service = ResizeService()
