"""
Transcription Service with Fallback
Handles video transcription using available backends
"""
import logging
import subprocess
import json
from pathlib import Path
from typing import Optional, List
import uuid

logger = logging.getLogger(__name__)

# Try to import clipsai, but don't fail if not available
CLIPSAI_AVAILABLE = False
try:
    from clipsai import Transcriber as ClipsAITranscriber
    CLIPSAI_AVAILABLE = True
    logger.info("ClipsAI Transcriber available")
except ImportError as e:
    logger.warning(f"ClipsAI not available: {e}. Using fallback transcription.")


class TranscriptionService:
    """Service for transcribing video/audio files"""
    
    def __init__(self):
        self._transcriber = None
    
    @property
    def is_available(self) -> bool:
        """Check if any transcription method is available"""
        return True  # We always have at least FFmpeg fallback
    
    def transcribe(
        self, 
        file_path: str | Path,
        language: Optional[str] = None,
        batch_size: int = 16
    ) -> dict:
        """
        Transcribe a video/audio file
        
        Args:
            file_path: Path to the media file
            language: ISO 639-1 language code (auto-detect if None)
            batch_size: WhisperX batch size (reduce if low on GPU memory)
        
        Returns:
            dict with transcription data including text, sentences, words
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        logger.info(f"Starting transcription for: {file_path.name}")
        
        if CLIPSAI_AVAILABLE:
            return self._transcribe_with_clipsai(file_path, language, batch_size)
        else:
            return self._transcribe_fallback(file_path, language)
    
    def _transcribe_with_clipsai(
        self, 
        file_path: Path, 
        language: Optional[str],
        batch_size: int
    ) -> dict:
        """Transcribe using ClipsAI/WhisperX"""
        if self._transcriber is None:
            self._transcriber = ClipsAITranscriber()
        
        transcription = self._transcriber.transcribe(
            audio_file_path=str(file_path.absolute()),
            iso6391_lang_code=language,
            batch_size=batch_size
        )
        
        logger.info(f"Transcription complete. Language: {transcription.language}")
        
        return {
            "text": transcription.text,
            "language": transcription.language,
            "start_time": transcription.start_time,
            "end_time": transcription.end_time,
            "sentences": [
                {
                    "text": s.text,
                    "start_time": s.start_time,
                    "end_time": s.end_time,
                    "start_char": s.start_char,
                    "end_char": s.end_char,
                }
                for s in transcription.sentences
            ],
            "words": [
                {
                    "text": w.text,
                    "start_time": w.start_time,
                    "end_time": w.end_time,
                }
                for w in transcription.words
            ],
            "_transcription_obj": transcription
        }
    
    def _transcribe_fallback(
        self, 
        file_path: Path, 
        language: Optional[str]
    ) -> dict:
        """
        Fallback transcription placeholder.
        In a real implementation, this would use a simpler whisper setup.
        For now, returns a mock transcription for testing.
        """
        logger.warning("Using fallback transcription (mock data)")
        
        # Get video duration using ffprobe
        duration = self._get_duration(file_path)
        
        # Create mock transcription data for UI testing
        mock_text = (
            "This is a placeholder transcription. "
            "The full ClipsAI transcription service is not available. "
            "Please install pyannote.audio for full functionality. "
            "This mock data allows you to test the UI workflow."
        )
        
        return {
            "text": mock_text,
            "language": language or "en",
            "start_time": 0.0,
            "end_time": duration,
            "sentences": [
                {
                    "text": mock_text,
                    "start_time": 0.0,
                    "end_time": duration,
                    "start_char": 0,
                    "end_char": len(mock_text),
                }
            ],
            "words": [
                {"text": word, "start_time": i * 0.5, "end_time": (i + 1) * 0.5}
                for i, word in enumerate(mock_text.split())
            ],
            "_transcription_obj": None,
            "_is_fallback": True,
        }
    
    def _get_duration(self, file_path: Path) -> float:
        """Get media duration using ffprobe"""
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "quiet", "-print_format", "json",
                    "-show_format", str(file_path)
                ],
                capture_output=True,
                text=True
            )
            data = json.loads(result.stdout)
            return float(data.get("format", {}).get("duration", 60.0))
        except Exception as e:
            logger.warning(f"Could not get duration: {e}")
            return 60.0
    
    def detect_language(self, file_path: str | Path) -> str:
        """Detect the language of a media file"""
        if CLIPSAI_AVAILABLE and self._transcriber:
            file_path = Path(file_path)
            return self._transcriber.detect_language(
                audio_file_path=str(file_path.absolute())
            )
        return "en"  # Default fallback


# Singleton instance
transcription_service = TranscriptionService()
