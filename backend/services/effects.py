"""
Effects & Music Service
Adds effects, transitions, and music to video clips
"""
import logging
from pathlib import Path
from typing import Optional, List
import subprocess

logger = logging.getLogger(__name__)


class EffectsService:
    """Service for adding effects and music to video clips"""
    
    # Built-in music tracks (royalty-free)
    MUSIC_TRACKS = {
        "upbeat": "upbeat_background.mp3",
        "chill": "chill_vibes.mp3",
        "dramatic": "dramatic_intro.mp3",
        "inspirational": "inspirational_rise.mp3",
    }
    
    def add_music(
        self,
        video_path: str | Path,
        output_path: str | Path,
        music_path: str | Path,
        music_volume: float = 0.3,
        fade_in: float = 1.0,
        fade_out: float = 2.0,
    ) -> Path:
        """
        Add background music to a video
        
        Args:
            video_path: Path to source video
            output_path: Path for output video
            music_path: Path to music file
            music_volume: Volume level for music (0.0 - 1.0)
            fade_in: Fade in duration in seconds
            fade_out: Fade out duration in seconds
        
        Returns:
            Path to the video with music
        """
        video_path = Path(video_path)
        output_path = Path(output_path)
        music_path = Path(music_path)
        
        # Get video duration
        duration = self._get_duration(video_path)
        
        # FFmpeg command to mix audio
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(music_path),
            "-filter_complex",
            f"[1:a]volume={music_volume},afade=t=in:st=0:d={fade_in},afade=t=out:st={duration-fade_out}:d={fade_out}[music];"
            f"[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        logger.info(f"Added music to: {output_path}")
        return output_path
    
    def add_fade_effects(
        self,
        video_path: str | Path,
        output_path: str | Path,
        fade_in: float = 0.5,
        fade_out: float = 0.5,
    ) -> Path:
        """
        Add fade in/out effects to video
        
        Args:
            video_path: Path to source video
            output_path: Path for output video
            fade_in: Fade in duration
            fade_out: Fade out duration
        
        Returns:
            Path to the video with fades
        """
        video_path = Path(video_path)
        output_path = Path(output_path)
        
        duration = self._get_duration(video_path)
        
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vf", f"fade=t=in:st=0:d={fade_in},fade=t=out:st={duration-fade_out}:d={fade_out}",
            "-af", f"afade=t=in:st=0:d={fade_in},afade=t=out:st={duration-fade_out}:d={fade_out}",
            "-c:v", "libx264",
            "-preset", "fast",
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        logger.info(f"Added fade effects to: {output_path}")
        return output_path
    
    def add_intro_text(
        self,
        video_path: str | Path,
        output_path: str | Path,
        text: str,
        duration: float = 3.0,
        font_size: int = 48,
    ) -> Path:
        """
        Add intro text overlay to video
        
        Args:
            video_path: Path to source video
            output_path: Path for output video
            text: Text to display
            duration: How long to show the text
        
        Returns:
            Path to the video with text overlay
        """
        video_path = Path(video_path)
        output_path = Path(output_path)
        
        # Escape special characters for FFmpeg
        text = text.replace("'", "\\'").replace(":", "\\:")
        
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vf", f"drawtext=text='{text}':fontsize={font_size}:fontcolor=white:borderw=2:bordercolor=black:x=(w-text_w)/2:y=(h-text_h)/2:enable='between(t,0,{duration})'",
            "-c:a", "copy",
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        logger.info(f"Added intro text to: {output_path}")
        return output_path
    
    def _get_duration(self, video_path: Path) -> float:
        """Get video duration in seconds"""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())


# Singleton instance
effects_service = EffectsService()
