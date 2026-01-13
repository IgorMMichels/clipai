"""
ClipsAI Clip Finding Service
Finds optimal clips using TextTiling algorithm
"""
import logging
from pathlib import Path
from typing import List, Optional
import uuid

logger = logging.getLogger(__name__)

# Check if clipsai clip finder is available
CLIPFINDER_AVAILABLE = False
try:
    from clipsai import ClipFinder as ClipsAIClipFinder
    CLIPFINDER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ClipsAI ClipFinder not available: {e}")


class ClipFinderService:
    """Service for finding clips in transcribed content"""
    
    def __init__(self):
        self._clip_finder = None
    
    @property
    def is_available(self) -> bool:
        """Check if clip finder is available"""
        return CLIPFINDER_AVAILABLE
    
    @property
    def clip_finder(self):
        """Lazy load the clip finder"""
        if self._clip_finder is None:
            if not CLIPFINDER_AVAILABLE:
                raise ImportError(
                    "ClipsAI ClipFinder not available. "
                    "Please install clipsai with: pip install clipsai"
                )
            self._clip_finder = ClipsAIClipFinder()
        return self._clip_finder
    
    def find_clips(
        self,
        transcription_obj,
        min_duration: float = 30.0,
        max_duration: float = 120.0,
    ) -> List[dict]:
        """
        Find clips from a transcription
        
        Args:
            transcription_obj: ClipsAI Transcription object
            min_duration: Minimum clip duration in seconds
            max_duration: Maximum clip duration in seconds
        
        Returns:
            List of clip dictionaries with timing and transcript info
        """
        if not CLIPFINDER_AVAILABLE:
            raise ImportError(
                "ClipsAI is not available. Cannot find clips. "
                "Install with: pip install clipsai"
            )
        
        logger.info("Finding clips using TextTiling algorithm...")
        
        # Find clips using ClipsAI
        clips = self.clip_finder.find_clips(transcription=transcription_obj)
        
        logger.info(f"Found {len(clips)} potential clips")
        
        # Process and filter clips
        processed_clips = []
        for clip in clips:
            duration = clip.end_time - clip.start_time
            
            # Filter by duration
            if duration < min_duration or duration > max_duration:
                continue
            
            # Extract transcript for this clip
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
