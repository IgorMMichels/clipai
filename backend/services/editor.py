"""
Video Editor Service
Handles trimming, resizing, and exporting clips
"""
import logging
from pathlib import Path
from typing import Optional, List, Dict
import subprocess

logger = logging.getLogger(__name__)


class VideoEditorService:
    """Service for editing and exporting video clips"""
    
    def trim_clip(
        self,
        input_path: str | Path,
        output_path: str | Path,
        start_time: float,
        end_time: float,
    ) -> Path:
        """
        Trim a video to create a clip
        
        Args:
            input_path: Path to source video
            output_path: Path for output clip
            start_time: Start time in seconds
            end_time: End time in seconds
        
        Returns:
            Path to the trimmed clip
        """
        import clipsai
        
        input_path = Path(input_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Trimming clip: {start_time:.2f}s - {end_time:.2f}s")
        
        media_editor = clipsai.MediaEditor()
        media_file = clipsai.AudioVideoFile(str(input_path.absolute()))
        
        clip_file = media_editor.trim(
            media_file=media_file,
            start_time=start_time,
            end_time=end_time,
            trimmed_media_file_path=str(output_path.absolute()),
        )
        
        logger.info(f"Clip saved to: {output_path}")
        return output_path
    
    def resize_video(
        self,
        input_path: str | Path,
        output_path: str | Path,
        crops_data: dict,
    ) -> Path:
        """
        Resize a video using crop data from ResizeService
        
        Args:
            input_path: Path to source video
            output_path: Path for output video
            crops_data: Crop information from resize service
        
        Returns:
            Path to the resized video
        """
        import clipsai
        
        input_path = Path(input_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Resizing video to {crops_data['crop_width']}x{crops_data['crop_height']}")
        
        media_editor = clipsai.MediaEditor()
        media_file = clipsai.AudioVideoFile(str(input_path.absolute()))
        
        resized_file = media_editor.resize_video(
            original_video_file=media_file,
            resized_video_file_path=str(output_path.absolute()),
            width=crops_data["crop_width"],
            height=crops_data["crop_height"],
            segments=crops_data["segments"],
        )
        
        logger.info(f"Resized video saved to: {output_path}")
        return output_path
    
    def add_subtitles(
        self,
        video_path: str | Path,
        output_path: str | Path,
        subtitles: List[dict],
        font_size: int = 24,
        font_color: str = "white",
        outline_color: str = "black",
    ) -> Path:
        """
        Burn subtitles into a video using FFmpeg
        
        Args:
            video_path: Path to source video
            output_path: Path for output video
            subtitles: List of subtitle dicts with text, start_time, end_time
        
        Returns:
            Path to the video with subtitles
        """
        video_path = Path(video_path)
        output_path = Path(output_path)
        
        # Create SRT file
        srt_path = output_path.with_suffix(".srt")
        self._create_srt(subtitles, srt_path)
        
        # Burn subtitles using FFmpeg
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vf", f"subtitles={srt_path}:force_style='FontSize={font_size},PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2'",
            "-c:a", "copy",
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Clean up SRT file
        srt_path.unlink(missing_ok=True)
        
        logger.info(f"Added subtitles to: {output_path}")
        return output_path
    
    def _create_srt(self, subtitles: List[dict], output_path: Path):
        """Create an SRT subtitle file"""
        def format_time(seconds: float) -> str:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            millis = int((seconds % 1) * 1000)
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
        
        with open(output_path, "w", encoding="utf-8") as f:
            for i, sub in enumerate(subtitles, 1):
                f.write(f"{i}\n")
                f.write(f"{format_time(sub['start_time'])} --> {format_time(sub['end_time'])}\n")
                f.write(f"{sub['text']}\n\n")


# Singleton instance
video_editor_service = VideoEditorService()
