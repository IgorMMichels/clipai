"""
Clip Finding Service with Fallback
Finds optimal clips using TextTiling algorithm or simple segmentation
"""
import logging
from pathlib import Path
from typing import List, Optional
import uuid

logger = logging.getLogger(__name__)

# Try to import clipsai, but don't fail if not available
CLIPSAI_AVAILABLE = False
try:
    from clipsai import ClipFinder as ClipsAIClipFinder
    CLIPSAI_AVAILABLE = True
    logger.info("ClipsAI ClipFinder available")
except ImportError as e:
    logger.warning(f"ClipsAI ClipFinder not available: {e}. Using fallback clip detection.")


class ClipFinderService:
    """Service for finding clips in transcribed content"""
    
    def __init__(self):
        self._clip_finder = None
    
    @property
    def is_available(self) -> bool:
        """Check if clip finding is available"""
        return True  # We always have at least fallback
    
    def find_clips(
        self,
        transcription_obj,
        min_duration: float = 30.0,
        max_duration: float = 120.0,
    ) -> List[dict]:
        """
        Find clips from a transcription
        
        Args:
            transcription_obj: ClipsAI Transcription object or dict
            min_duration: Minimum clip duration in seconds
            max_duration: Maximum clip duration in seconds
        
        Returns:
            List of clip dictionaries with timing and transcript info
        """
        logger.info("Finding clips...")
        
        # Check if we have a ClipsAI transcription object
        if CLIPSAI_AVAILABLE and transcription_obj is not None and hasattr(transcription_obj, 'words'):
            return self._find_clips_clipsai(transcription_obj, min_duration, max_duration)
        else:
            return self._find_clips_fallback(transcription_obj, min_duration, max_duration)
    
    def _find_clips_clipsai(
        self,
        transcription_obj,
        min_duration: float,
        max_duration: float,
    ) -> List[dict]:
        """Find clips using ClipsAI's TextTiling algorithm"""
        if self._clip_finder is None:
            self._clip_finder = ClipsAIClipFinder()
        
        clips = self._clip_finder.find_clips(transcription=transcription_obj)
        
        logger.info(f"Found {len(clips)} potential clips")
        
        processed_clips = []
        for clip in clips:
            duration = clip.end_time - clip.start_time
            
            if duration < min_duration or duration > max_duration:
                continue
            
            clip_transcript = self._extract_clip_transcript(
                transcription_obj, 
                clip.start_time, 
                clip.end_time
            )
            
            processed_clips.append({
                "id": str(uuid.uuid4()),
                "start_time": clip.start_time,
                "end_time": clip.end_time,
                "duration": duration,
                "start_char": clip.start_char,
                "end_char": clip.end_char,
                "transcript": clip_transcript,
            })
        
        logger.info(f"Returning {len(processed_clips)} clips after filtering")
        return processed_clips
    
    def _find_clips_fallback(
        self,
        transcription_data: dict,
        min_duration: float,
        max_duration: float,
    ) -> List[dict]:
        """
        Fallback clip detection using simple time-based segmentation.
        Divides the video into segments based on duration preferences.
        """
        logger.warning("Using fallback clip detection (simple segmentation)")
        
        # Handle both dict and object transcription data
        if isinstance(transcription_data, dict):
            total_duration = transcription_data.get("end_time", 300.0)
            full_text = transcription_data.get("text", "")
        else:
            total_duration = getattr(transcription_data, "end_time", 300.0)
            full_text = getattr(transcription_data, "text", "")
        
        clips = []
        
        # Create clips at regular intervals
        target_duration = (min_duration + max_duration) / 2  # 75 seconds default
        
        current_time = 0.0
        clip_index = 0
        
        while current_time < total_duration:
            clip_end = min(current_time + target_duration, total_duration)
            clip_duration = clip_end - current_time
            
            if clip_duration >= min_duration:
                # Calculate approximate text for this clip
                text_start = int((current_time / total_duration) * len(full_text))
                text_end = int((clip_end / total_duration) * len(full_text))
                clip_text = full_text[text_start:text_end].strip()
                
                if not clip_text:
                    clip_text = f"Clip {clip_index + 1} from {current_time:.1f}s to {clip_end:.1f}s"
                
                clips.append({
                    "id": str(uuid.uuid4()),
                    "start_time": current_time,
                    "end_time": clip_end,
                    "duration": clip_duration,
                    "start_char": text_start,
                    "end_char": text_end,
                    "transcript": clip_text,
                })
                clip_index += 1
            
            current_time = clip_end
        
        logger.info(f"Created {len(clips)} clips using fallback segmentation")
        return clips
    
    def _extract_clip_transcript(
        self,
        transcription,
        start_time: float,
        end_time: float
    ) -> str:
        """Extract transcript text for a specific time range"""
        words = []
        for word in transcription.words:
            if word.start_time >= start_time and word.end_time <= end_time:
                words.append(word.text)
        return " ".join(words)


# Singleton instance
clip_finder_service = ClipFinderService()
