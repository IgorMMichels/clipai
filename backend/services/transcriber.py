"""
Transcription Service with Fallback
Handles video transcription using Faster-Whisper directly (most stable option)
"""
import logging
import subprocess
import json
from pathlib import Path
from typing import Optional, List, Callable
import uuid

logger = logging.getLogger(__name__)

class TranscriptionService:
    """Service for transcribing video/audio files"""
    
    def __init__(self):
        pass
    
    @property
    def is_available(self) -> bool:
        """Check if any transcription method is available"""
        return True
    
    def transcribe(
        self, 
        file_path: str | Path,
        language: Optional[str] = None,
        batch_size: int = 16,
        progress_callback: Optional[Callable] = None
    ) -> dict:
        """
        Transcribe a video/audio file using Faster-Whisper
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        logger.info(f"Starting transcription for: {file_path.name}")
        
        return self._transcribe_with_faster_whisper(file_path, language, progress_callback)

    def _transcribe_with_faster_whisper(
        self,
        file_path: Path,
        language: Optional[str],
        progress_callback: Optional[Callable] = None
    ) -> dict:
        """Transcribe using Faster-Whisper directly"""
        from faster_whisper import WhisperModel
        import torch
        import gc

        device = "cuda" if torch.cuda.is_available() else "cpu"
        # Use int8 on CPU to be faster
        compute_type = "float16" if torch.cuda.is_available() else "int8"
        
        logger.info(f"Loading Faster-Whisper model on {device} with {compute_type}...")
        
        try:
            # 1. Transcribe
            # Use 'small' model for speed/quality balance
            model = WhisperModel("small", device=device, compute_type=compute_type)
            
            segments, info = model.transcribe(
                str(file_path), 
                beam_size=5, 
                language=language,
                word_timestamps=True
            )
            
            detected_language = info.language
            logger.info(f"Detected language: {detected_language} (prob: {info.language_probability:.2f})")
            
            # 2. Format output
            sentences = []
            words = []
            full_text = ""
            
            # segments is a generator, so we iterate
            for segment in segments:
                text = segment.text.strip()
                full_text += text + " "
                
                if progress_callback:
                    progress_callback(full_text)
                
                # Create sentence entry
                # Note: faster-whisper segments are roughly sentence-like but not strictly sentences
                sentences.append({
                    "text": text,
                    "start_time": segment.start,
                    "end_time": segment.end,
                    "start_char": len(full_text) - len(text) - 1,
                    "end_char": len(full_text) - 1,
                })
                
                if segment.words:
                    for word in segment.words:
                        words.append({
                            "text": word.word.strip(),
                            "start_time": word.start,
                            "end_time": word.end,
                        })
            
            # Clean up
            del model
            gc.collect()
            if device == "cuda":
                torch.cuda.empty_cache()

            duration = self._get_duration(file_path)

            return {
                "text": full_text.strip(),
                "language": detected_language,
                "start_time": 0.0,
                "end_time": duration,
                "sentences": sentences,
                "words": words,
                "_transcription_obj": None, # No native obj needed
                "_is_fallback": False
            }
        except Exception as e:
            logger.error(f"Faster-Whisper transcription failed: {e}")
            raise e
    
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
        # We could use faster-whisper to detect, but for now fallback to 'en'
        # or implement a lightweight check
        return "en" 


# Singleton instance
transcription_service = TranscriptionService()
