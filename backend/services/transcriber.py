"""
Transcription Service with Faster-Whisper and AI Optimization
Enhanced with VAD filtering and OpenAI text optimization
Inspired by AI-Video-Transcriber: https://github.com/wendy7756/AI-Video-Transcriber
"""
import logging
import subprocess
import json
import os
from pathlib import Path
from typing import Optional, List, Callable
import asyncio

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Service for transcribing video/audio files with AI optimization"""
    
    def __init__(self, model_size: str = "small"):
        """
        Initialize transcriber
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
        """
        self.model_size = model_size
        self.model = None
        self.last_detected_language = None
        self._openai_client = None
    
    @property
    def is_available(self) -> bool:
        """Check if transcription is available"""
        return True
    
    def _load_model(self, device: str = "cpu", compute_type: str = "int8"):
        """Lazy load the Whisper model"""
        if self.model is None:
            from faster_whisper import WhisperModel
            logger.info(f"Loading Faster-Whisper model: {self.model_size} on {device}")
            try:
                self.model = WhisperModel(
                    self.model_size, 
                    device=device, 
                    compute_type=compute_type
                )
                logger.info("Whisper model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                raise
    
    def _get_openai_client(self):
        """Get or create OpenAI client"""
        if self._openai_client is None:
            try:
                from openai import OpenAI
                api_key = os.environ.get("OPENAI_API_KEY")
                base_url = os.environ.get("OPENAI_BASE_URL")
                
                if api_key:
                    self._openai_client = OpenAI(
                        api_key=api_key,
                        base_url=base_url if base_url else None
                    )
                    logger.info("OpenAI client initialized")
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI: {e}")
        return self._openai_client
    
    def transcribe(
        self, 
        file_path: str | Path,
        language: Optional[str] = None,
        batch_size: int = 16,
        progress_callback: Optional[Callable] = None,
        optimize_with_ai: bool = True,
    ) -> dict:
        """
        Transcribe a video/audio file using Faster-Whisper
        
        Args:
            file_path: Path to media file
            language: Language code (None for auto-detect)
            batch_size: Batch size for processing
            progress_callback: Callback for progress updates
            optimize_with_ai: Whether to optimize transcript with GPT
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        logger.info(f"Starting transcription for: {file_path.name}")
        
        result = self._transcribe_with_faster_whisper(file_path, language, progress_callback)
        
        # Optionally optimize with AI
        if optimize_with_ai and result.get("text"):
            try:
                optimized = self._optimize_with_ai(result["text"], result.get("language", "en"))
                if optimized:
                    result["text_original"] = result["text"]
                    result["text"] = optimized
                    result["_ai_optimized"] = True
                    logger.info("Transcript optimized with AI")
            except Exception as e:
                logger.warning(f"AI optimization failed: {e}")
                result["_ai_optimized"] = False
        
        return result

    def _transcribe_with_faster_whisper(
        self,
        file_path: Path,
        language: Optional[str],
        progress_callback: Optional[Callable] = None
    ) -> dict:
        """Transcribe using Faster-Whisper with optimized parameters"""
        import gc

        # Try to detect CUDA availability with graceful fallback
        try:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            compute_type = "float16" if torch.cuda.is_available() else "int8"
            logger.info(f"Using device: {device}, compute_type: {compute_type}")
        except ImportError:
            logger.warning("torch not available, using CPU with int8")
            device = "cpu"
            compute_type = "int8"
        except Exception as e:
            logger.warning(f"Error detecting CUDA: {e}, using CPU with int8")
            device = "cpu"
            compute_type = "int8"
        
        try:
            # Load model
            self._load_model(device, compute_type)
            
            # Transcribe with optimized parameters from AI-Video-Transcriber
            segments, info = self.model.transcribe(
                str(file_path), 
                language=language,
                beam_size=5,
                best_of=5,
                temperature=[0.0, 0.2, 0.4],  # Temperature fallback strategy
                word_timestamps=True,
                # VAD filtering for better accuracy
                vad_filter=True,
                vad_parameters={
                    "min_silence_duration_ms": 500,  # Minimum silence duration
                    "speech_pad_ms": 200,  # Speech padding
                },
                no_speech_threshold=0.6,  # No speech threshold
                compression_ratio_threshold=2.4,  # Detect repetition
                log_prob_threshold=-1.0,
                condition_on_previous_text=False,  # Avoid error accumulation
            )
            
            detected_language = info.language
            self.last_detected_language = detected_language
            logger.info(f"Detected language: {detected_language} (prob: {info.language_probability:.2f})")
            
            # Format output
            sentences = []
            words = []
            full_text = ""
            char_offset = 0
            
            for segment in segments:
                text = segment.text.strip()
                if not text:
                    continue
                    
                full_text += text + " "
                
                if progress_callback:
                    progress_callback(full_text)
                
                # Create sentence entry
                sentences.append({
                    "text": text,
                    "start_time": segment.start,
                    "end_time": segment.end,
                    "start_char": char_offset,
                    "end_char": char_offset + len(text),
                })
                char_offset = len(full_text)
                
                # Extract word-level timestamps
                if segment.words:
                    for word in segment.words:
                        word_text = word.word.strip()
                        if word_text:
                            words.append({
                                "text": word_text,
                                "start_time": word.start,
                                "end_time": word.end,
                            })
            
            # Get duration
            duration = self._get_duration(file_path)

            return {
                "text": full_text.strip(),
                "language": detected_language,
                "language_probability": info.language_probability,
                "start_time": 0.0,
                "end_time": duration,
                "sentences": sentences,
                "words": words,
                "_transcription_obj": None,
                "_is_fallback": False,
            }
            
        except Exception as e:
            logger.error(f"Faster-Whisper transcription failed: {e}")
            raise
        finally:
            # Clean up GPU memory
            gc.collect()
            if device == "cuda":
                try:
                    import torch
                    torch.cuda.empty_cache()
                except:
                    pass
    
    def _optimize_with_ai(self, text: str, language: str) -> Optional[str]:
        """
        Optimize transcript using OpenAI GPT
        - Fix typos and grammar
        - Complete incomplete sentences
        - Improve punctuation
        """
        client = self._get_openai_client()
        if not client:
            return None
        
        # Don't optimize very short texts
        if len(text) < 50:
            return None
        
        try:
            # Truncate if too long (GPT has limits)
            max_chars = 12000
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
            
            system_prompt = """You are a transcript editor. Your task is to:
1. Fix obvious typos and transcription errors
2. Add proper punctuation where missing
3. Fix grammatical errors
4. Keep the original meaning and tone
5. Do NOT add new content or change the meaning
6. Return ONLY the corrected text, no explanations"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Fast and cheap
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Please correct this transcript ({language}):\n\n{text}"}
                ],
                temperature=0.3,
                max_tokens=4000,
            )
            
            optimized = response.choices[0].message.content
            return optimized.strip() if optimized else None
            
        except Exception as e:
            logger.warning(f"AI optimization error: {e}")
            return None
    
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
        if self.last_detected_language:
            return self.last_detected_language
        return "en"
    
    def get_supported_languages(self) -> list:
        """Get list of supported languages"""
        return [
            "en", "zh", "es", "fr", "de", "it", "pt", "ru", "ja", "ko",
            "ar", "hi", "th", "vi", "tr", "pl", "nl", "sv", "da", "no",
            "fi", "cs", "hu", "ro", "bg", "uk", "hr", "sk", "sl", "et",
        ]


# Singleton instance
transcription_service = TranscriptionService(model_size="small")
