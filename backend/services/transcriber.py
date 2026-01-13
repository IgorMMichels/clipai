"""
ClipsAI Transcription Service
Handles video transcription using WhisperX
"""
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Check if clipsai transcription is available
TRANSCRIPTION_AVAILABLE = False
try:
    from clipsai import Transcriber as ClipsAITranscriber
    TRANSCRIPTION_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ClipsAI Transcriber not available: {e}")


class TranscriptionService:
    """Service for transcribing video/audio files using ClipsAI/WhisperX"""
    
    def __init__(self):
        self._transcriber = None
    
    @property
    def is_available(self) -> bool:
        """Check if transcription is available"""
        return TRANSCRIPTION_AVAILABLE
    
    @property
    def transcriber(self):
        """Lazy load the transcriber to avoid import overhead"""
        if self._transcriber is None:
            if not TRANSCRIPTION_AVAILABLE:
                raise ImportError(
                    "ClipsAI Transcriber not available. "
                    "Please install clipsai with: pip install clipsai"
                )
            self._transcriber = ClipsAITranscriber()
        return self._transcriber
    
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
        
        if not TRANSCRIPTION_AVAILABLE:
            raise ImportError(
                "ClipsAI is not available. Cannot transcribe. "
                "Install with: pip install clipsai"
            )
        
        logger.info(f"Starting transcription for: {file_path.name}")
        
        # Transcribe using ClipsAI
        transcription = self.transcriber.transcribe(
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
            "_transcription_obj": transcription  # Keep original for ClipFinder
        }
    
    def detect_language(self, file_path: str | Path) -> str:
        """Detect the language of a media file"""
        file_path = Path(file_path)
        return self.transcriber.detect_language(
            audio_file_path=str(file_path.absolute())
        )


# Singleton instance
transcription_service = TranscriptionService()
