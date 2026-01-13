"""
Video Editor Service
Handles trimming, resizing, and exporting clips using MoviePy and FFmpeg
"""
import logging
import uuid
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
        fps: int = 60,
    ) -> Path:
        """
        Resize a video using crop data (dynamic cropping)
        Using MoviePy for easier segment handling
        """
        from moviepy import VideoFileClip, concatenate_videoclips
        
        input_path = Path(input_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Resizing video to {crops_data['crop_width']}x{crops_data['crop_height']} at {fps} fps")
        
        clip = VideoFileClip(str(input_path))
        subclips = []
        
        segments = crops_data.get("segments", [])
        cw = crops_data.get("crop_width", clip.w)
        ch = crops_data.get("crop_height", clip.h)
        
        if not segments:
             logger.warning("No segments for resizing, doing center crop")
             subclips.append(clip.resized(height=ch).cropped(width=cw, height=ch, x_center=clip.w/2, y_center=clip.h/2))
        else:
            for seg in segments:
                # Segment times are relative to the start of the trimmed clip (0-based)
                start = seg["start_time"]
                end = seg["end_time"] if seg.get("end_time") is not None else clip.duration
                
                # Ensure we don't go out of bounds
                end = min(end, clip.duration)
                if start >= end:
                    continue
                    
                # Crop
                # x, y are top-left coordinates
                x1 = int(seg.get("x", 0))
                y1 = int(seg.get("y", 0))
                
                # Crop using moviepy
                sub = clip.subclipped(start, end).cropped(x1=x1, y1=y1, width=cw, height=ch)
                subclips.append(sub)
            
        if subclips:
            final_clip = concatenate_videoclips(subclips)
        else:
            final_clip = clip.resized(height=ch).cropped(width=cw, height=ch, x_center=clip.w/2, y_center=clip.h/2)
        
        # Write output
        final_clip.write_videofile(
            str(output_path),
            fps=fps,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=str(output_path.with_suffix(".m4a")),
            remove_temp=True,
            logger=None, # Silence logger
            preset="medium",
            bitrate="8000k"
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
    
    def apply_stacked_layout(
        self,
        input_path: str | Path,
        output_path: str | Path,
        crops_data: dict,
        fps: int = 60,
    ) -> Path:
        """
        Apply a stacked layout: Top = Gameplay (centered), Bottom = Face (cropped)
        Exports at specified FPS (default 60) and FHD (1080x1920)
        """
        from moviepy import VideoFileClip, concatenate_videoclips, CompositeVideoClip, ColorClip
        
        input_path = Path(input_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Applying stacked layout to: {input_path} at {fps} fps")
        
        # Load clip
        clip = VideoFileClip(str(input_path))
        
        # Target Dimensions for 9:16
        target_w = 1080
        target_h = 1920
        
        # 1. Top Part: Gameplay
        # Scale original to width 1080
        gameplay = clip.resized(width=target_w)
        
        # 2. Bottom Part: Face Crop
        # Generate the face clip using crops_data
        subclips = []
        segments = crops_data.get("segments", [])
        cw = crops_data.get("crop_width", clip.w)
        ch = crops_data.get("crop_height", clip.h)
        
        # If no segments provided, just use the whole clip centered
        if not segments:
             logger.warning("No segments for resizing, using center crop for bottom")
             subclips.append(clip.resized(height=ch).cropped(width=cw, height=ch, x_center=clip.w/2, y_center=clip.h/2))
        else:
            for seg in segments:
                start = seg["start_time"]
                end = seg["end_time"] if seg.get("end_time") is not None else clip.duration
                end = min(end, clip.duration)
                if start >= end: continue
                
                x1 = int(seg.get("x", 0))
                y1 = int(seg.get("y", 0))
                
                # Crop using moviepy
                sub = clip.subclipped(start, end).cropped(x1=x1, y1=y1, width=cw, height=ch)
                subclips.append(sub)

        if subclips:
            face_clip = concatenate_videoclips(subclips)
        else:
             # Fallback
             face_clip = clip.resized(height=ch).cropped(width=cw, height=ch, x_center=clip.w/2, y_center=clip.h/2)
        
        # Resize face_clip to width 1080
        face_clip = face_clip.resized(width=target_w)
        
        # Position face_clip at bottom
        face_clip = face_clip.with_position(("center", "bottom"))
        gameplay = gameplay.with_position(("center", "top"))
        
        # Create final composite
        final = CompositeVideoClip([gameplay, face_clip], size=(target_w, target_h))
        
        final.write_videofile(
            str(output_path),
            fps=fps,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=str(output_path.with_suffix(".m4a")),
            remove_temp=True,
            logger=None,
            preset="medium",  # Better quality
            bitrate="8000k"   # High bitrate for FHD
        )
        
        clip.close()
        gameplay.close()
        face_clip.close()
        final.close()
        
        return output_path


    def process_viral_clip(
        self,
        input_path: str | Path,
        output_path: str | Path,
        start_time: float,
        end_time: float,
        crops_data: dict,
        subtitles: List[dict],
        fps: int = 60
    ) -> Path:
        """
        Full pipeline: Trim -> Stacked Layout (9:16, 60fps) -> Burn Subtitles
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        # Temporary files
        temp_trim = output_path.with_name(f"temp_trim_{uuid.uuid4()}{input_path.suffix}")
        temp_layout = output_path.with_name(f"temp_layout_{uuid.uuid4()}{input_path.suffix}")
        
        try:
            # 1. Trim (Fast cut)
            # using ffmpeg to trim first saves processing time in moviepy
            self.trim_clip(input_path, temp_trim, start_time, end_time)
            
            # 2. Adjust Data for Trimmed Clip
            # Crops segments: shift by -start_time
            adjusted_crops = crops_data.copy()
            adjusted_segments = []
            if "segments" in crops_data:
                for seg in crops_data["segments"]:
                    # check if segment overlaps with the clip
                    seg_start = seg["start_time"]
                    seg_end = seg["end_time"] if seg.get("end_time") is not None else end_time
                    
                    if seg_end <= start_time or seg_start >= end_time:
                        continue
                        
                    # Clamp and Shift
                    new_start = max(0.0, seg_start - start_time)
                    new_end = min(end_time - start_time, seg_end - start_time)
                    
                    new_seg = seg.copy()
                    new_seg["start_time"] = new_start
                    new_seg["end_time"] = new_end
                    adjusted_segments.append(new_seg)
            
            adjusted_crops["segments"] = adjusted_segments
            
            # Subtitles: shift by -start_time and filter
            adjusted_subtitles = []
            for sub in subtitles:
                sub_start = sub["start_time"]
                sub_end = sub["end_time"]
                
                if sub_end <= start_time or sub_start >= end_time:
                    continue
                    
                new_start = max(0.0, sub_start - start_time)
                new_end = min(end_time - start_time, sub_end - start_time)
                
                new_sub = sub.copy()
                new_sub["start_time"] = new_start
                new_sub["end_time"] = new_end
                adjusted_subtitles.append(new_sub)

            # 3. Apply Layout
            # result is saved to temp_layout
            self.apply_stacked_layout(
                input_path=temp_trim,
                output_path=temp_layout,
                crops_data=adjusted_crops,
                fps=fps
            )
            
            # 4. Burn Subtitles
            # result is saved to output_path
            self.add_subtitles(
                video_path=temp_layout,
                output_path=output_path,
                subtitles=adjusted_subtitles
            )
            
        except Exception as e:
            logger.error(f"Error processing viral clip: {e}")
            raise e
        finally:
            # Cleanup
            if temp_trim.exists():
                temp_trim.unlink()
            if temp_layout.exists():
                temp_layout.unlink()
                
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
