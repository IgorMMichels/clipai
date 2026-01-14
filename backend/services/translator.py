"""
Translation Service
Translates transcripts between languages using LLM APIs
Inspired by AI-Video-Transcriber: https://github.com/wendy7756/AI-Video-Transcriber
"""
import logging
import os
import json
import re
from typing import Optional, List

logger = logging.getLogger(__name__)


# Language codes and their full names
SUPPORTED_LANGUAGES = {
    "en": "English",
    "zh": "Chinese (Simplified)",
    "zh-TW": "Chinese (Traditional)",
    "ja": "Japanese",
    "ko": "Korean",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "pt": "Portuguese",
    "pt-BR": "Portuguese (Brazilian)",
    "ru": "Russian",
    "ar": "Arabic",
    "hi": "Hindi",
    "it": "Italian",
    "nl": "Dutch",
    "pl": "Polish",
    "tr": "Turkish",
    "vi": "Vietnamese",
    "th": "Thai",
    "id": "Indonesian",
    "ms": "Malay",
    "uk": "Ukrainian",
    "cs": "Czech",
    "sv": "Swedish",
    "da": "Danish",
    "no": "Norwegian",
    "fi": "Finnish",
    "el": "Greek",
    "he": "Hebrew",
    "hu": "Hungarian",
    "ro": "Romanian",
    "bg": "Bulgarian",
}


class TranslatorService:
    """Service for translating transcripts between languages"""
    
    def __init__(
        self,
        google_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
    ):
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self._gemini_model = None
        self._openai_client = None
        self._anthropic_client = None
    
    @property
    def gemini_model(self):
        """Lazy load Gemini model"""
        if self._gemini_model is None and self.google_api_key:
            import google.generativeai as genai
            genai.configure(api_key=self.google_api_key)
            self._gemini_model = genai.GenerativeModel('gemini-2.0-flash')
        return self._gemini_model
    
    @property
    def openai_client(self):
        """Lazy load OpenAI client"""
        if self._openai_client is None and self.openai_api_key:
            from openai import OpenAI
            base_url = os.environ.get("OPENAI_BASE_URL")
            self._openai_client = OpenAI(
                api_key=self.openai_api_key,
                base_url=base_url if base_url else None
            )
        return self._openai_client
    
    @property
    def anthropic_client(self):
        """Lazy load Anthropic client"""
        if self._anthropic_client is None and self.anthropic_api_key:
            from anthropic import Anthropic
            self._anthropic_client = Anthropic(api_key=self.anthropic_api_key)
        return self._anthropic_client
    
    def get_supported_languages(self) -> dict:
        """Get list of supported languages for translation"""
        return SUPPORTED_LANGUAGES.copy()
    
    def detect_language(self, text: str) -> str:
        """
        Detect the language of a given text
        
        Args:
            text: Text to detect language for
            
        Returns:
            Language code (e.g., "en", "zh", "ja")
        """
        if not text or len(text.strip()) < 10:
            return "en"
        
        # Use a sample of the text for detection
        sample = text[:1000]
        
        prompt = f"""Detect the language of this text and respond with ONLY the ISO 639-1 language code (e.g., "en", "zh", "ja", "es", "fr", "de", "pt", "ru", "ar", "ko").

Text: {sample}

Respond with ONLY the 2-letter language code, nothing else."""

        try:
            if self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=10,
                )
                lang = response.choices[0].message.content.strip().lower()
                # Validate it's a proper code
                if lang in SUPPORTED_LANGUAGES or len(lang) == 2:
                    return lang
            elif self.gemini_model:
                response = self.gemini_model.generate_content(prompt)
                lang = response.text.strip().lower()
                if lang in SUPPORTED_LANGUAGES or len(lang) == 2:
                    return lang
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
        
        # Fallback: Simple heuristics
        return self._detect_language_heuristic(text)
    
    def _detect_language_heuristic(self, text: str) -> str:
        """Simple heuristic-based language detection"""
        # Check for CJK characters
        cjk_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        hiragana_katakana = sum(1 for c in text if '\u3040' <= c <= '\u30ff')
        hangul = sum(1 for c in text if '\uac00' <= c <= '\ud7af')
        arabic = sum(1 for c in text if '\u0600' <= c <= '\u06ff')
        cyrillic = sum(1 for c in text if '\u0400' <= c <= '\u04ff')
        
        text_len = len(text)
        if text_len == 0:
            return "en"
        
        if hangul / text_len > 0.1:
            return "ko"
        if hiragana_katakana / text_len > 0.1:
            return "ja"
        if cjk_chars / text_len > 0.1:
            return "zh"
        if arabic / text_len > 0.1:
            return "ar"
        if cyrillic / text_len > 0.1:
            return "ru"
        
        return "en"
    
    def translate(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None,
        preserve_formatting: bool = True,
    ) -> dict:
        """
        Translate text to target language
        
        Args:
            text: Text to translate
            target_language: Target language code (e.g., "en", "zh")
            source_language: Source language code (auto-detect if None)
            preserve_formatting: Whether to preserve paragraph structure
        
        Returns:
            dict with translated_text, source_language, target_language
        """
        if not text or len(text.strip()) < 10:
            return {
                "translated_text": text,
                "source_language": source_language or "unknown",
                "target_language": target_language,
                "source_language_name": SUPPORTED_LANGUAGES.get(source_language, "Unknown"),
                "target_language_name": SUPPORTED_LANGUAGES.get(target_language, "English"),
            }
        
        # Detect source language if not provided
        if not source_language:
            source_language = self.detect_language(text)
        
        # Skip if already in target language
        if source_language == target_language:
            return {
                "translated_text": text,
                "source_language": source_language,
                "target_language": target_language,
                "source_language_name": SUPPORTED_LANGUAGES.get(source_language, "Unknown"),
                "target_language_name": SUPPORTED_LANGUAGES.get(target_language, "English"),
                "_skipped": True,
            }
        
        source_name = SUPPORTED_LANGUAGES.get(source_language, source_language)
        target_name = SUPPORTED_LANGUAGES.get(target_language, target_language)
        
        formatting_instruction = ""
        if preserve_formatting:
            formatting_instruction = "Preserve paragraph breaks and formatting. "
        
        prompt = f"""Translate the following text from {source_name} to {target_name}.

Instructions:
- {formatting_instruction}
- Maintain the original meaning and tone
- Keep proper nouns unchanged when appropriate
- Do not add explanations or notes
- Return ONLY the translated text

Text to translate:
{text[:12000]}"""

        try:
            # Priority: OpenAI -> Gemini -> Anthropic (OpenAI often has better translations)
            if self.openai_client:
                logger.info(f"Translating with OpenAI: {source_language} -> {target_language}")
                translated = self._translate_with_openai(prompt)
            elif self.gemini_model:
                logger.info(f"Translating with Gemini: {source_language} -> {target_language}")
                translated = self._translate_with_gemini(prompt)
            elif self.anthropic_client:
                logger.info(f"Translating with Anthropic: {source_language} -> {target_language}")
                translated = self._translate_with_anthropic(prompt)
            else:
                logger.warning("No LLM API key configured for translation")
                return {
                    "translated_text": "",
                    "source_language": source_language,
                    "target_language": target_language,
                    "source_language_name": source_name,
                    "target_language_name": target_name,
                    "error": "No translation service available",
                }
            
            return {
                "translated_text": translated,
                "source_language": source_language,
                "target_language": target_language,
                "source_language_name": source_name,
                "target_language_name": target_name,
            }
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return {
                "translated_text": "",
                "source_language": source_language,
                "target_language": target_language,
                "source_language_name": source_name,
                "target_language_name": target_name,
                "error": str(e),
            }
    
    def _translate_with_openai(self, prompt: str) -> str:
        """Translate using OpenAI GPT"""
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional translator. Provide accurate, natural translations."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    
    def _translate_with_gemini(self, prompt: str) -> str:
        """Translate using Google Gemini"""
        response = self.gemini_model.generate_content(prompt)
        return response.text.strip()
    
    def _translate_with_anthropic(self, prompt: str) -> str:
        """Translate using Anthropic Claude"""
        response = self.anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
    
    def translate_with_timestamps(
        self,
        segments: List[dict],
        target_language: str,
        source_language: Optional[str] = None,
    ) -> List[dict]:
        """
        Translate transcript segments while preserving timestamps
        
        Args:
            segments: List of segments with 'text', 'start_time', 'end_time'
            target_language: Target language code
            source_language: Source language code (auto-detect if None)
        
        Returns:
            List of translated segments with preserved timestamps
        """
        if not segments:
            return []
        
        # Detect source language from first few segments
        if not source_language:
            sample_text = " ".join(s.get("text", "") for s in segments[:10])
            source_language = self.detect_language(sample_text)
        
        # Skip if same language
        if source_language == target_language:
            return segments
        
        # Batch translate for efficiency
        translated_segments = []
        batch_size = 20  # Translate 20 segments at a time
        
        for i in range(0, len(segments), batch_size):
            batch = segments[i:i + batch_size]
            
            # Create numbered text for translation
            numbered_texts = [f"{j+1}. {s.get('text', '')}" for j, s in enumerate(batch)]
            combined_text = "\n".join(numbered_texts)
            
            source_name = SUPPORTED_LANGUAGES.get(source_language, source_language)
            target_name = SUPPORTED_LANGUAGES.get(target_language, target_language)
            
            prompt = f"""Translate these numbered sentences from {source_name} to {target_name}.
Keep the numbering format exactly. Only translate the text after each number.

{combined_text}"""

            try:
                if self.openai_client:
                    translated = self._translate_with_openai(prompt)
                elif self.gemini_model:
                    translated = self._translate_with_gemini(prompt)
                elif self.anthropic_client:
                    translated = self._translate_with_anthropic(prompt)
                else:
                    # No translation available, return original
                    translated_segments.extend(batch)
                    continue
                
                # Parse translated lines
                lines = translated.strip().split("\n")
                translations = {}
                for line in lines:
                    match = re.match(r'^(\d+)\.\s*(.+)$', line.strip())
                    if match:
                        idx = int(match.group(1)) - 1
                        translations[idx] = match.group(2)
                
                # Apply translations to segments
                for j, segment in enumerate(batch):
                    new_segment = segment.copy()
                    if j in translations:
                        new_segment["text_original"] = segment.get("text", "")
                        new_segment["text"] = translations[j]
                    translated_segments.append(new_segment)
                    
            except Exception as e:
                logger.error(f"Batch translation error: {e}")
                # Return original on error
                translated_segments.extend(batch)
        
        return translated_segments


# Singleton instance
translator_service = TranslatorService()
