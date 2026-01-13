"""
Video Editor Service
Handles trimming, resizing, and exporting clips using MoviePy and FFmpeg
"""
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import subprocess
import os

logger = logging.getLogger(__name__)

class VideoEditorService:
    """Service for editing and exporting video clips"""
    
    def generate_preview(
        self,
        input_path: str | Path,
        output_path: str | Path,
        start_time: float,
        end_time: float,
        aspect_ratio: tuple[int, int] = (9, 16),
    ) -> Path:
        """
        Generate a fast, low-quality preview clip using FFmpeg
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Calculate dimensions (approximate 360p base)
        target_w, target_h = aspect_ratio
        # Keep it small for preview
        if target_h > target_w:
            h = 640
            w = int(h * (target_w / target_h))
        else:
            w = 640
            h = int(w * (target_h / target_w))
            
        w = w if w % 2 == 0 else w + 1
        h = h if h % 2 == 0 else h + 1
        
        duration = end_time - start_time
        
        # Center crop filter
        # scale to cover, then crop
        vf = f"scale='if(gt(iw/ih,{w}/{h}),-1,{w})':'if(gt(iw/ih,{w}/{h}),{h},-1)',crop={w}:{h}"
        
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_time),
            "-i", str(input_path),
            "-t", str(duration),
            "-vf", vf,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "30",
            "-c:a", "aac",
            str(output_path)
        ]
        
        logger.info(f"Generating preview: {output_path}")
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path

    def trim_clip(
        self,
        input_path: str | Path,
        output_path: str | Path,
        start_time: float,
        end_time: float,
    ) -> Path:
        """
        Trim a video to create a clip using FFmpeg (re-encode for accuracy)
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        duration = end_time - start_time
        
        logger.info(f"Trimming clip: {start_time:.2f}s - {end_time:.2f}s")
        
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_time),
            "-i", str(input_path),
            "-t", str(duration),
            "-c:v", "libx264",
            "-preset", "fast",
            "-c:a", "aac",
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path
    
    def resize_video(
        self,
        input_path: str | Path,
        output_path: str | Path,
        crops_data: dict,
    ) -> Path:
        """
        Resize a video using crop data (dynamic cropping)
        Using MoviePy for easier segment handling
        """
        from moviepy import VideoFileClip, concatenate_videoclips
        
        input_path = Path(input_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Resizing video to {crops_data['crop_width']}x{crops_data['crop_height']}")
        
        clip = VideoFileClip(str(input_path))
        subclips = []
        
        segments = crops_data["segments"]
        cw = crops_data["crop_width"]
        ch = crops_data["crop_height"]
        
        for seg in segments:
            # Segment times are relative to the start of the trimmed clip (0-based)
            # or absolute if passed from resizer? 
            # Resizer receives the trimmed clip, so times are 0-based relative to that clip.
            start = seg["start_time"]
            end = seg["end_time"] if seg["end_time"] is not None else clip.duration
            
            # Ensure we don't go out of bounds
            end = min(end, clip.duration)
            if start >= end:
                continue
                
            # Crop
            # x, y are top-left coordinates
            x1 = int(seg["x"])
            y1 = int(seg["y"])
            
            # Crop using moviepy
            # crop(x1=None, y1=None, x2=None, y2=None, width=None, height=None, x_center=None, y_center=None)
            sub = clip.subclipped(start, end).cropped(x1=x1, y1=y1, width=cw, height=ch)
            subclips.append(sub)
            
        if not subclips:
            # Fallback if no segments found
             logger.warning("No segments for resizing, doing center crop")
             subclips.append(clip.resized(height=ch).cropped(width=cw, height=ch, x_center=clip.w/2, y_center=clip.h/2))

        final_clip = concatenate_videoclips(subclips)
        
        # Write output
        final_clip.write_videofile(
            str(output_path),
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=str(output_path.with_suffix(".m4a")),
            remove_temp=True,
            logger=None # Silence logger
        )
        
        clip.close()
        final_clip.close()
        
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
        """
        video_path = Path(video_path)
        output_path = Path(output_path)
        
        # Create SRT file
        srt_path = output_path.with_suffix(".srt")
        self._create_srt(subtitles, srt_path)
        
        # Burn subtitles using FFmpeg
        # Escape path for filter
        srt_path_str = str(srt_path).replace("\\", "/").replace(":", "\\:")
        
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vf", f"subtitles='{srt_path_str}':force_style='FontSize={font_size},PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2'",
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
