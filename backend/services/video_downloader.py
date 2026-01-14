"""
Multi-Platform Video Download Service
Downloads videos from 30+ platforms using yt-dlp
Supports YouTube, TikTok, Bilibili, Instagram, Twitter, and many more
Inspired by AI-Video-Transcriber: https://github.com/wendy7756/AI-Video-Transcriber
"""
import logging
import yt_dlp
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
import re

logger = logging.getLogger(__name__)


# Supported platforms with their extractors
SUPPORTED_PLATFORMS = {
    "youtube": {
        "name": "YouTube",
        "patterns": [r"youtube\.com", r"youtu\.be"],
        "extractor": "youtube",
    },
    "tiktok": {
        "name": "TikTok",
        "patterns": [r"tiktok\.com", r"vm\.tiktok\.com"],
        "extractor": "tiktok",
    },
    "bilibili": {
        "name": "Bilibili",
        "patterns": [r"bilibili\.com", r"b23\.tv"],
        "extractor": "bilibili",
    },
    "instagram": {
        "name": "Instagram",
        "patterns": [r"instagram\.com"],
        "extractor": "instagram",
    },
    "twitter": {
        "name": "Twitter/X",
        "patterns": [r"twitter\.com", r"x\.com"],
        "extractor": "twitter",
    },
    "facebook": {
        "name": "Facebook",
        "patterns": [r"facebook\.com", r"fb\.watch"],
        "extractor": "facebook",
    },
    "vimeo": {
        "name": "Vimeo",
        "patterns": [r"vimeo\.com"],
        "extractor": "vimeo",
    },
    "dailymotion": {
        "name": "Dailymotion",
        "patterns": [r"dailymotion\.com"],
        "extractor": "dailymotion",
    },
    "twitch": {
        "name": "Twitch",
        "patterns": [r"twitch\.tv", r"clips\.twitch\.tv"],
        "extractor": "twitch",
    },
    "reddit": {
        "name": "Reddit",
        "patterns": [r"reddit\.com", r"v\.redd\.it"],
        "extractor": "reddit",
    },
    "linkedin": {
        "name": "LinkedIn",
        "patterns": [r"linkedin\.com"],
        "extractor": "linkedin",
    },
    "pinterest": {
        "name": "Pinterest",
        "patterns": [r"pinterest\.com", r"pin\.it"],
        "extractor": "pinterest",
    },
    "tumblr": {
        "name": "Tumblr",
        "patterns": [r"tumblr\.com"],
        "extractor": "tumblr",
    },
    "soundcloud": {
        "name": "SoundCloud",
        "patterns": [r"soundcloud\.com"],
        "extractor": "soundcloud",
    },
    "youku": {
        "name": "Youku",
        "patterns": [r"youku\.com"],
        "extractor": "youku",
    },
    "iqiyi": {
        "name": "iQIYI",
        "patterns": [r"iqiyi\.com"],
        "extractor": "iqiyi",
    },
    "tencent": {
        "name": "Tencent Video",
        "patterns": [r"v\.qq\.com"],
        "extractor": "tencentvideo",
    },
    "weibo": {
        "name": "Weibo",
        "patterns": [r"weibo\.com"],
        "extractor": "weibo",
    },
    "nicovideo": {
        "name": "Niconico",
        "patterns": [r"nicovideo\.jp", r"nico\.ms"],
        "extractor": "niconico",
    },
    "vlive": {
        "name": "VLive",
        "patterns": [r"vlive\.tv"],
        "extractor": "vlive",
    },
    "pornhub": {
        "name": "Pornhub",
        "patterns": [r"pornhub\.com"],
        "extractor": "pornhub",
    },
    "xvideos": {
        "name": "XVideos",
        "patterns": [r"xvideos\.com"],
        "extractor": "xvideos",
    },
    "vk": {
        "name": "VK",
        "patterns": [r"vk\.com"],
        "extractor": "vk",
    },
    "ok_ru": {
        "name": "Odnoklassniki",
        "patterns": [r"ok\.ru"],
        "extractor": "ok.ru",
    },
    "rutube": {
        "name": "Rutube",
        "patterns": [r"rutube\.ru"],
        "extractor": "rutube",
    },
    "naver": {
        "name": "Naver",
        "patterns": [r"tv\.naver\.com"],
        "extractor": "naver",
    },
    "kakao": {
        "name": "Kakao",
        "patterns": [r"tv\.kakao\.com"],
        "extractor": "kakao",
    },
}


class VideoDownloaderService:
    """Service for downloading videos from multiple platforms using yt-dlp"""
    
    def __init__(self):
        self._extractors_info = None
    
    def get_supported_platforms(self) -> List[Dict[str, str]]:
        """Get list of supported platforms"""
        return [
            {"id": key, "name": value["name"]}
            for key, value in SUPPORTED_PLATFORMS.items()
        ]
    
    def detect_platform(self, url: str) -> Optional[str]:
        """
        Detect which platform a URL belongs to
        
        Args:
            url: Video URL
            
        Returns:
            Platform identifier or None if not recognized
        """
        url_lower = url.lower()
        for platform_id, info in SUPPORTED_PLATFORMS.items():
            for pattern in info["patterns"]:
                if re.search(pattern, url_lower):
                    return platform_id
        return None
    
    def get_video_info(self, url: str) -> Dict[str, Any]:
        """
        Get video metadata without downloading
        
        Args:
            url: Video URL
            
        Returns:
            Dict with video metadata
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                platform = self.detect_platform(url)
                
                return {
                    "title": info.get("title", "Unknown"),
                    "duration": info.get("duration", 0),
                    "uploader": info.get("uploader") or info.get("channel") or "Unknown",
                    "view_count": info.get("view_count", 0),
                    "like_count": info.get("like_count", 0),
                    "thumbnail": info.get("thumbnail", ""),
                    "description": info.get("description", ""),
                    "upload_date": info.get("upload_date", ""),
                    "platform": platform,
                    "platform_name": SUPPORTED_PLATFORMS.get(platform, {}).get("name", "Unknown"),
                    "webpage_url": info.get("webpage_url", url),
                    "extractor": info.get("extractor", ""),
                    "format": info.get("format", ""),
                    "resolution": f"{info.get('width', 0)}x{info.get('height', 0)}",
                }
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            raise Exception(f"Failed to get video info: {str(e)}")
    
    def download_video(
        self,
        url: str,
        output_path: Path,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        format_preference: str = "best",
        max_resolution: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Download video from URL
        
        Args:
            url: Video URL
            output_path: Path to save video (without extension)
            progress_callback: Optional callback for progress updates (progress%, status_message)
            format_preference: Format preference ("best", "audio_only", "720p", "1080p")
            max_resolution: Maximum resolution height (e.g., 1080)
            
        Returns:
            Dict with video metadata
        """
        # Ensure directory exists
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Remove extension if present (yt-dlp adds it)
        output_template = str(output_path.with_suffix(''))
        
        # Configure format based on preference
        format_string = self._get_format_string(format_preference, max_resolution)
        
        # Progress hook
        def progress_hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0:
                    progress = (downloaded / total) * 100
                    if progress_callback:
                        speed = d.get('speed', 0)
                        speed_str = f"{speed / 1024 / 1024:.1f} MB/s" if speed else ""
                        progress_callback(progress, f"Downloading... {speed_str}")
            elif d['status'] == 'finished':
                if progress_callback:
                    progress_callback(100, "Download complete, processing...")
        
        ydl_opts = {
            'format': format_string,
            'merge_output_format': 'mp4',
            'outtmpl': output_template + '.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [progress_hook],
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            # Handle age-restricted content
            'age_limit': None,
            # Retry on failure
            'retries': 3,
            'fragment_retries': 3,
            # Better error handling
            'ignoreerrors': False,
            'no_abort_on_error': False,
        }
        
        # Add cookies for platforms that need authentication
        platform = self.detect_platform(url)
        if platform in ['instagram', 'facebook']:
            # These platforms may need cookies for some content
            pass
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info(f"Downloading video from {platform or 'unknown platform'}: {url}")
                info = ydl.extract_info(url, download=True)
                
                # Find the actual downloaded file
                downloaded_file = self._find_downloaded_file(output_path.parent, output_template)
                
                return {
                    "title": info.get("title", "Unknown"),
                    "duration": info.get("duration", 0),
                    "uploader": info.get("uploader") or info.get("channel") or "Unknown",
                    "view_count": info.get("view_count", 0),
                    "like_count": info.get("like_count", 0),
                    "thumbnail": info.get("thumbnail", ""),
                    "description": info.get("description", ""),
                    "upload_date": info.get("upload_date", ""),
                    "platform": platform,
                    "platform_name": SUPPORTED_PLATFORMS.get(platform, {}).get("name", "Unknown"),
                    "downloaded_file": str(downloaded_file) if downloaded_file else str(output_path),
                    "file_size": downloaded_file.stat().st_size if downloaded_file and downloaded_file.exists() else 0,
                }
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            logger.error(f"Download error: {error_msg}")
            
            # Provide helpful error messages
            if "Private video" in error_msg:
                raise Exception("This video is private and cannot be downloaded.")
            elif "Video unavailable" in error_msg:
                raise Exception("This video is unavailable. It may have been deleted or restricted.")
            elif "age" in error_msg.lower():
                raise Exception("This video is age-restricted. Authentication may be required.")
            elif "copyright" in error_msg.lower():
                raise Exception("This video cannot be downloaded due to copyright restrictions.")
            else:
                raise Exception(f"Failed to download video: {error_msg}")
        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            raise Exception(f"Failed to download video: {str(e)}")
    
    def _get_format_string(self, preference: str, max_resolution: Optional[int] = None) -> str:
        """Get yt-dlp format string based on preference"""
        if preference == "audio_only":
            return "bestaudio/best"
        
        if max_resolution:
            return f"bestvideo[height<={max_resolution}]+bestaudio/best[height<={max_resolution}]/best"
        
        if preference == "720p":
            return "bestvideo[height<=720]+bestaudio/best[height<=720]/best"
        elif preference == "1080p":
            return "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"
        elif preference == "4k":
            return "bestvideo[height<=2160]+bestaudio/best[height<=2160]/best"
        
        # Default: best quality
        return "bestvideo+bestaudio/best"
    
    def _find_downloaded_file(self, directory: Path, base_name: str) -> Optional[Path]:
        """Find the downloaded file (yt-dlp may add extension)"""
        base = Path(base_name).name
        for ext in ['.mp4', '.webm', '.mkv', '.mov', '.avi', '.mp3', '.m4a']:
            candidate = directory / f"{base}{ext}"
            if candidate.exists():
                return candidate
        
        # Check for any file starting with the base name
        for file in directory.iterdir():
            if file.name.startswith(base) and file.is_file():
                return file
        
        return None
    
    def download_audio_only(
        self,
        url: str,
        output_path: Path,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Download only audio from video URL
        
        Args:
            url: Video URL
            output_path: Path to save audio
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dict with audio metadata
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        output_template = str(output_path.with_suffix(''))
        
        def progress_hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0 and progress_callback:
                    progress = (downloaded / total) * 100
                    progress_callback(progress, "Downloading audio...")
            elif d['status'] == 'finished':
                if progress_callback:
                    progress_callback(100, "Processing audio...")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template + '.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [progress_hook],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info(f"Downloading audio: {url}")
                info = ydl.extract_info(url, download=True)
                
                # Find the audio file
                audio_file = self._find_downloaded_file(output_path.parent, output_template)
                
                return {
                    "title": info.get("title", "Unknown"),
                    "duration": info.get("duration", 0),
                    "uploader": info.get("uploader") or info.get("channel") or "Unknown",
                    "downloaded_file": str(audio_file) if audio_file else str(output_path.with_suffix('.mp3')),
                    "platform": self.detect_platform(url),
                }
        except Exception as e:
            logger.error(f"Error downloading audio: {e}")
            raise Exception(f"Failed to download audio: {str(e)}")


# Singleton instance
video_downloader_service = VideoDownloaderService()

# Keep backward compatibility with youtube_service
youtube_service = video_downloader_service
