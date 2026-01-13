"""
LLM Description Generator Service
Generates social media descriptions for clips using Gemini, OpenAI or Anthropic
"""
import logging
from typing import Optional, List
import os
import json
import re

logger = logging.getLogger(__name__)


class DescriptionGeneratorService:
    """Service for generating video descriptions using LLMs"""
    
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
        if self._openai_client is None and self.openai_api_key:
            from openai import OpenAI
            self._openai_client = OpenAI(api_key=self.openai_api_key)
        return self._openai_client
    
    @property
    def anthropic_client(self):
        if self._anthropic_client is None and self.anthropic_api_key:
            from anthropic import Anthropic
            self._anthropic_client = Anthropic(api_key=self.anthropic_api_key)
        return self._anthropic_client
    
    def generate_description(
        self,
        transcript: str,
        language: str = "en",
        style: str = "social_media",
        max_length: int = 200,
        include_hashtags: bool = True,
    ) -> dict:
        """
        Generate a description for a video clip
        
        Args:
            transcript: The clip's transcript
            language: Output language ("en" for English, "pt" for Portuguese)
            style: Description style ("social_media", "professional", "casual")
            max_length: Maximum character length
            include_hashtags: Whether to include hashtags
        
        Returns:
            dict with description and hashtags
        """
        language_name = "English" if language == "en" else "Portuguese"
        
        style_instructions = {
            "social_media": "engaging, with emojis and a hook. Make it viral-worthy.",
            "professional": "professional and informative. Focus on value and insights.",
            "casual": "friendly and conversational. Keep it light and relatable.",
        }
        
        prompt = f"""Based on this video transcript, generate a social media description.

Language: {language_name}
Style: {style_instructions.get(style, style_instructions['social_media'])}
Max length: {max_length} characters
Include hashtags: {include_hashtags}

Transcript:
{transcript[:2000]}

Respond ONLY with valid JSON in this exact format (no markdown, no code blocks):
{{"description": "your description here", "hashtags": ["hashtag1", "hashtag2", "hashtag3"]}}"""

        try:
            # Priority: Gemini -> OpenAI -> Anthropic -> Fallback
            if self.gemini_model:
                logger.info("Using Gemini 2.0 Flash for description generation")
                return self._generate_with_gemini(prompt)
            elif self.openai_client:
                logger.info("Using OpenAI for description generation")
                return self._generate_with_openai(prompt)
            elif self.anthropic_client:
                logger.info("Using Anthropic for description generation")
                return self._generate_with_anthropic(prompt)
            else:
                logger.warning("No LLM API key configured, using fallback")
                return self._generate_fallback(transcript, language)
        except Exception as e:
            logger.error(f"Error generating description: {e}")
            return self._generate_fallback(transcript, language)
    
    def _generate_with_gemini(self, prompt: str) -> dict:
        """Generate description using Google Gemini"""
        response = self.gemini_model.generate_content(prompt)
        text = response.text.strip()
        
        # Clean up response (remove markdown code blocks if present)
        if text.startswith("```"):
            text = re.sub(r'^```(?:json)?\n?', '', text)
            text = re.sub(r'\n?```$', '', text)
        
        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON in the response
            match = re.search(r'\{[^}]+\}', text, re.DOTALL)
            if match:
                result = json.loads(match.group())
            else:
                result = {"description": text[:200], "hashtags": []}
        
        return {
            "description": result.get("description", ""),
            "hashtags": result.get("hashtags", []),
        }
    
    def _generate_with_openai(self, prompt: str) -> dict:
        """Generate description using OpenAI"""
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a social media expert. Generate engaging video descriptions. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=300,
        )
        
        result = json.loads(response.choices[0].message.content)
        return {
            "description": result.get("description", ""),
            "hashtags": result.get("hashtags", []),
        }
    
    def _generate_with_anthropic(self, prompt: str) -> dict:
        """Generate description using Anthropic Claude"""
        response = self.anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=300,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )
        
        # Parse JSON from response
        text = response.content[0].text
        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON in the response
            match = re.search(r'\{[^}]+\}', text, re.DOTALL)
            if match:
                result = json.loads(match.group())
            else:
                result = {"description": text, "hashtags": []}
        
        return {
            "description": result.get("description", ""),
            "hashtags": result.get("hashtags", []),
        }
    
    def _generate_fallback(self, transcript: str, language: str) -> dict:
        """Fallback description generator (no LLM)"""
        # Take first sentence as description
        first_sentence = transcript.split(".")[0][:150] if transcript else ""
        
        if language == "pt":
            description = f"Confira este momento incrivel! {first_sentence}..."
            hashtags = ["viral", "brasil", "fyp", "trending"]
        else:
            description = f"Check out this amazing moment! {first_sentence}..."
            hashtags = ["viral", "fyp", "trending", "mustwatch"]
        
        return {
            "description": description,
            "hashtags": hashtags,
        }


# Singleton instance
description_service = DescriptionGeneratorService()
