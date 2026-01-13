"""
YouTube Download Service
"""
import logging
import yt_dlp
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

class YouTubeService:
    """Service for downloading videos from YouTube"""
    
    def download_video(self, url: str, output_path: Path) -> Dict[str, Any]:
        """
        Download video from YouTube
        
        Args:
            url: YouTube URL
            output_path: Path to save video
            
        Returns:
            Dict with video metadata
        """
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure yt-dlp
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': str(output_path),
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info(f"Downloading YouTube video: {url}")
                info = ydl.extract_info(url, download=True)
                
                return {
                    "title": info.get("title", "Unknown"),
                    "duration": info.get("duration", 0),
                    "uploader": info.get("uploader", "Unknown"),
                    "view_count": info.get("view_count", 0),
                    "thumbnail": info.get("thumbnail", ""),
                    "description": info.get("description", ""),
                }
        except Exception as e:
            logger.error(f"Error downloading YouTube video: {e}")
            raise Exception(f"Failed to download video: {str(e)}")

# Singleton instance
youtube_service = YouTubeService()
