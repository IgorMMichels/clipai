"""
AI Summary Generation Service
Generates intelligent summaries of transcripts in multiple languages
Inspired by AI-Video-Transcriber: https://github.com/wendy7756/AI-Video-Transcriber
"""
import logging
import os
import json
import re
from typing import Optional, List

logger = logging.getLogger(__name__)


# Supported summary languages with their full names
SUMMARY_LANGUAGES = {
    "en": "English",
    "zh": "Chinese (Simplified)",
    "ja": "Japanese",
    "ko": "Korean",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "pt": "Portuguese",
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
}


class SummarizerService:
    """Service for generating AI-powered summaries of transcripts"""
    
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
        """Get list of supported summary languages"""
        return SUMMARY_LANGUAGES.copy()
    
    def summarize(
        self,
        transcript: str,
        language: str = "en",
        style: str = "comprehensive",
        max_length: int = 500,
        include_key_points: bool = True,
    ) -> dict:
        """
        Generate an AI-powered summary of a transcript
        
        Args:
            transcript: The full transcript text
            language: Output language code (e.g., "en", "zh", "ja")
            style: Summary style ("comprehensive", "brief", "bullet_points")
            max_length: Maximum character length (approximate)
            include_key_points: Whether to extract key points
        
        Returns:
            dict with summary, key_points, and metadata
        """
        if not transcript or len(transcript.strip()) < 50:
            return self._empty_summary(language)
        
        language_name = SUMMARY_LANGUAGES.get(language, "English")
        
        style_instructions = {
            "comprehensive": f"Create a comprehensive summary in {language_name}. Cover main topics, key insights, and conclusions.",
            "brief": f"Create a brief, concise summary in {language_name}. Focus only on the most essential points.",
            "bullet_points": f"Create a bullet-point summary in {language_name}. List the main points clearly.",
        }
        
        prompt = f"""Summarize the following transcript.

Output language: {language_name}
Style: {style_instructions.get(style, style_instructions['comprehensive'])}
Maximum length: approximately {max_length} characters for the summary

Transcript:
{transcript[:15000]}

Respond ONLY with valid JSON in this exact format (no markdown, no code blocks):
{{
    "summary": "your summary here in {language_name}",
    "key_points": ["point 1", "point 2", "point 3"],
    "topics": ["topic1", "topic2"],
    "sentiment": "positive/neutral/negative"
}}"""

        try:
            # Priority: Gemini -> OpenAI -> Anthropic -> Fallback
            if self.gemini_model:
                logger.info("Using Gemini for summary generation")
                return self._summarize_with_gemini(prompt, language)
            elif self.openai_client:
                logger.info("Using OpenAI for summary generation")
                return self._summarize_with_openai(prompt, language)
            elif self.anthropic_client:
                logger.info("Using Anthropic for summary generation")
                return self._summarize_with_anthropic(prompt, language)
            else:
                logger.warning("No LLM API key configured, using fallback")
                return self._summarize_fallback(transcript, language)
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return self._summarize_fallback(transcript, language)
    
    def _summarize_with_gemini(self, prompt: str, language: str) -> dict:
        """Generate summary using Google Gemini"""
        response = self.gemini_model.generate_content(prompt)
        text = response.text.strip()
        return self._parse_summary_response(text, language)
    
    def _summarize_with_openai(self, prompt: str, language: str) -> dict:
        """Generate summary using OpenAI"""
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert summarizer. Create clear, accurate summaries. Respond only with valid JSON."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=1000,
        )
        
        result = json.loads(response.choices[0].message.content)
        return self._format_summary_result(result, language)
    
    def _summarize_with_anthropic(self, prompt: str, language: str) -> dict:
        """Generate summary using Anthropic Claude"""
        response = self.anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        
        text = response.content[0].text
        return self._parse_summary_response(text, language)
    
    def _parse_summary_response(self, text: str, language: str) -> dict:
        """Parse LLM response and extract summary data"""
        # Clean up response (remove markdown code blocks if present)
        if text.startswith("```"):
            text = re.sub(r'^```(?:json)?\n?', '', text)
            text = re.sub(r'\n?```$', '', text)
        
        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON in the response
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try:
                    result = json.loads(match.group())
                except json.JSONDecodeError:
                    result = {"summary": text[:500], "key_points": [], "topics": []}
            else:
                result = {"summary": text[:500], "key_points": [], "topics": []}
        
        return self._format_summary_result(result, language)
    
    def _format_summary_result(self, result: dict, language: str) -> dict:
        """Format the summary result with consistent structure"""
        return {
            "summary": result.get("summary", ""),
            "key_points": result.get("key_points", []),
            "topics": result.get("topics", []),
            "sentiment": result.get("sentiment", "neutral"),
            "language": language,
            "language_name": SUMMARY_LANGUAGES.get(language, "English"),
        }
    
    def _summarize_fallback(self, transcript: str, language: str) -> dict:
        """Fallback summary generator (no LLM)"""
        # Simple extractive summary: take first few sentences
        sentences = transcript.replace("...", ".").split(".")
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        # Take first 3-5 sentences as summary
        summary_sentences = sentences[:5]
        summary = ". ".join(summary_sentences)
        if summary and not summary.endswith("."):
            summary += "."
        
        # Extract potential key points (sentences with key indicators)
        key_indicators = ["important", "key", "main", "first", "second", "finally", "conclusion"]
        key_points = []
        for sentence in sentences[:15]:
            if any(indicator in sentence.lower() for indicator in key_indicators):
                key_points.append(sentence)
            if len(key_points) >= 3:
                break
        
        return {
            "summary": summary[:500] if summary else "No summary available.",
            "key_points": key_points,
            "topics": [],
            "sentiment": "neutral",
            "language": language,
            "language_name": SUMMARY_LANGUAGES.get(language, "English"),
            "_is_fallback": True,
        }
    
    def _empty_summary(self, language: str) -> dict:
        """Return empty summary structure"""
        return {
            "summary": "",
            "key_points": [],
            "topics": [],
            "sentiment": "neutral",
            "language": language,
            "language_name": SUMMARY_LANGUAGES.get(language, "English"),
        }


# Singleton instance
summarizer_service = SummarizerService()
