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
        subtitles: Optional[List[dict]] = None,
    ) -> Path:
        """
        Generate a fast preview clip with optional viral-style subtitles
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Calculate dimensions (720p for reasonable preview quality)
        target_w, target_h = aspect_ratio
        if target_h > target_w:
            h = 1280  # 720p height for vertical
            w = int(h * (target_w / target_h))
        else:
            w = 1280
            h = int(w * (target_h / target_w))
            
        w = w if w % 2 == 0 else w + 1
        h = h if h % 2 == 0 else h + 1
        
        duration = end_time - start_time
        
        # Build filter chain
        # Scale to cover, then crop
        vf_parts = [f"scale='if(gt(iw/ih,{w}/{h}),-1,{w})':'if(gt(iw/ih,{w}/{h}),{h},-1)'", f"crop={w}:{h}"]
        
        # Add subtitles if provided
        ass_path = None
        if subtitles and len(subtitles) > 0:
            ass_path = output_path.with_suffix(".ass")
            self._create_viral_ass(subtitles, ass_path, start_time, w, h)
            # Escape path for FFmpeg filter
            ass_path_escaped = str(ass_path).replace("\\", "/").replace(":", "\\:")
            vf_parts.append(f"ass='{ass_path_escaped}'")
        
        vf = ",".join(vf_parts)
        
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_time),
            "-i", str(input_path),
            "-t", str(duration),
            "-vf", vf,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            str(output_path)
        ]
        
        logger.info(f"Generating preview with subtitles: {output_path}")
        try:
            result = subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr.decode()}")
            raise
        finally:
            # Cleanup ASS file
            if ass_path and ass_path.exists():
                ass_path.unlink()
        
        return output_path
    
    def _create_viral_ass(self, subtitles: List[dict], output_path: Path, offset: float, width: int, height: int):
        """Create viral-style ASS subtitles with word-by-word highlighting"""
        def format_time(seconds: float) -> str:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            cs = int((seconds % 1) * 100)
            return f"{hours:1d}:{minutes:02d}:{secs:02d}.{cs:02d}"
        
        # Scale font size based on resolution
        font_size = max(40, int(height / 20))
        margin_v = int(height * 0.12)  # 12% from bottom
        
        header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Viral,Arial Black,{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,20,20,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        # Viral style: White text, black outline (4px), slight shadow
        # PrimaryColour &H00FFFFFF = white
        # OutlineColour &H00000000 = black  
        # BackColour &H80000000 = semi-transparent black shadow
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(header)
            for sub in subtitles:
                # Adjust time relative to clip start
                start = max(0, sub['start_time'] - offset)
                end = max(0, sub['end_time'] - offset)
                
                if end <= 0 or start >= end:
                    continue
                
                start_str = format_time(start)
                end_str = format_time(end)
                text = sub['text'].upper()  # Viral style is usually uppercase
                
                f.write(f"Dialogue: 0,{start_str},{end_str},Viral,,0,0,0,,{text}\n")

    def trim_clip(
        self,
        input_path: str | Path,
        output_path: str | Path,
        start_time: float,
        end_time: float,
    ) -> Path:
        """
        Trim a video to create a clip using FFmpeg (re-encode for accuracy and high quality)
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
            "-preset", "slow",     # Better compression efficiency
            "-crf", "18",          # Visually lossless
            "-c:a", "aac",
            "-b:a", "192k",        # High audio quality
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
        font_size: int = 24, # Ignored for ASS currently as we hardcode style
        font_color: str = "white",
        outline_color: str = "black",
    ) -> Path:
        """
        Burn subtitles into a video using FFmpeg and ASS format for viral style
        """
        video_path = Path(video_path)
        output_path = Path(output_path)
        
        # Create ASS file
        ass_path = output_path.with_suffix(".ass")
        self._create_ass(subtitles, ass_path)
        
        # Burn subtitles using FFmpeg
        # Escape path for filter
        ass_path_str = str(ass_path).replace("\\", "/").replace(":", "\\:")
        
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vf", f"ass='{ass_path_str}'",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "20",  # High quality
            "-c:a", "copy",
            str(output_path)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg subtitle burning failed: {e.stderr.decode()}")
            raise e
        
        # Clean up ASS file
        ass_path.unlink(missing_ok=True)
        
        logger.info(f"Added subtitles to: {output_path}")
        return output_path

    def _create_ass(self, subtitles: List[dict], output_path: Path):
        """Create an ASS subtitle file for viral word-by-word style"""
        def format_time(seconds: float) -> str:
            # H:MM:SS.cc
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            # centiseconds
            cs = int((seconds % 1) * 100)
            return f"{hours:1d}:{minutes:02d}:{secs:02d}.{cs:02d}"
        
        header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,80,&H0000FFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,3,0,2,10,10,250,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        # Style explanation:
        # Fontsize 80 (big)
        # PrimaryColour &H0000FFFF (Yellow in ASS BGR format -> 00 FFFF) - wait, standard is BGR? 
        # Yes, ASS is &HAABBGGRR. Yellow is R=FF, G=FF, B=00. So &H0000FFFF.
        # Outline: 3px Black (&H00000000)
        # Alignment: 2 (Bottom Center)
        # MarginV: 250 (Raised from bottom)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(header)
            for sub in subtitles:
                start = format_time(sub['start_time'])
                end = format_time(sub['end_time'])
                text = sub['text']
                # Highlight in Yellow (Default)
                # We could add animation or karaoke here, but simple word flash is good for now.
                f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n")

    
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

    def apply_pip_layout(
        self,
        input_path: str | Path,
        output_path: str | Path,
        facecam_region: dict,
        pip_position: str = "bottom-right",
        pip_scale: float = 0.25,
        fps: int = 60,
    ) -> Path:
        """
        Apply Picture-in-Picture layout: Main content with facecam overlay
        
        Args:
            input_path: Source video path
            output_path: Output video path
            facecam_region: Dict with x, y, width, height of facecam region
            pip_position: Where to place PiP (top-left, top-right, bottom-left, bottom-right)
            pip_scale: Scale of PiP relative to output width (0.25 = 25%)
            fps: Output framerate
        """
        from moviepy import VideoFileClip, CompositeVideoClip
        
        input_path = Path(input_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Applying PiP layout to: {input_path}")
        
        clip = VideoFileClip(str(input_path))
        
        # Target dimensions for 9:16
        target_w = 1080
        target_h = 1920
        
        # Extract facecam region
        fc_x = facecam_region.get("x", 0)
        fc_y = facecam_region.get("y", 0)
        fc_w = facecam_region.get("width", clip.w // 4)
        fc_h = facecam_region.get("height", clip.h // 4)
        
        # Ensure bounds are within frame
        fc_x = max(0, min(fc_x, clip.w - fc_w))
        fc_y = max(0, min(fc_y, clip.h - fc_h))
        fc_w = min(fc_w, clip.w - fc_x)
        fc_h = min(fc_h, clip.h - fc_y)
        
        # Crop facecam from original
        facecam_clip = clip.cropped(x1=fc_x, y1=fc_y, width=fc_w, height=fc_h)
        
        # Scale facecam for PiP
        pip_width = int(target_w * pip_scale)
        facecam_clip = facecam_clip.resized(width=pip_width)
        
        # Create main content (resize to fill 9:16, center crop if needed)
        # Calculate scale to cover the target
        scale_w = target_w / clip.w
        scale_h = target_h / clip.h
        scale = max(scale_w, scale_h)
        
        main_clip = clip.resized(scale)
        # Center crop
        main_clip = main_clip.cropped(
            x_center=main_clip.w / 2,
            y_center=main_clip.h / 2,
            width=target_w,
            height=target_h
        )
        
        # Position PiP
        margin = 40
        if pip_position == "top-left":
            pip_pos = (margin, margin)
        elif pip_position == "top-right":
            pip_pos = (target_w - pip_width - margin, margin)
        elif pip_position == "bottom-left":
            pip_pos = (margin, target_h - facecam_clip.h - margin)
        else:  # bottom-right
            pip_pos = (target_w - pip_width - margin, target_h - facecam_clip.h - margin)
        
        facecam_clip = facecam_clip.with_position(pip_pos)
        
        # Composite
        final = CompositeVideoClip([main_clip, facecam_clip], size=(target_w, target_h))
        
        final.write_videofile(
            str(output_path),
            fps=fps,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=str(output_path.with_suffix(".m4a")),
            remove_temp=True,
            logger=None,
            preset="medium",
            bitrate="8000k"
        )
        
        clip.close()
        facecam_clip.close()
        main_clip.close()
        final.close()
        
        logger.info(f"PiP layout saved to: {output_path}")
        return output_path

    def process_viral_clip_with_pip(
        self,
        input_path: str | Path,
        output_path: str | Path,
        start_time: float,
        end_time: float,
        facecam_region: Optional[dict],
        subtitles: List[dict],
        pip_position: str = "bottom-right",
        pip_scale: float = 0.25,
        fps: int = 60
    ) -> Path:
        """
        Full pipeline with PiP: Trim -> PiP Layout -> Burn Subtitles
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        temp_trim = output_path.with_name(f"temp_trim_{uuid.uuid4()}{input_path.suffix}")
        temp_pip = output_path.with_name(f"temp_pip_{uuid.uuid4()}{input_path.suffix}")
        
        try:
            # 1. Trim
            self.trim_clip(input_path, temp_trim, start_time, end_time)
            
            # 2. Apply PiP layout if facecam detected
            if facecam_region:
                self.apply_pip_layout(
                    input_path=temp_trim,
                    output_path=temp_pip,
                    facecam_region=facecam_region,
                    pip_position=pip_position,
                    pip_scale=pip_scale,
                    fps=fps
                )
            else:
                # No facecam, just resize to 9:16
                self._resize_to_vertical(temp_trim, temp_pip, fps)
            
            # 3. Adjust subtitles timing
            adjusted_subtitles = []
            for sub in subtitles:
                sub_start = sub.get("start_time", 0)
                sub_end = sub.get("end_time", 0)
                
                if sub_end <= start_time or sub_start >= end_time:
                    continue
                
                new_start = max(0.0, sub_start - start_time)
                new_end = min(end_time - start_time, sub_end - start_time)
                
                adjusted_subtitles.append({
                    "text": sub.get("text", ""),
                    "start_time": new_start,
                    "end_time": new_end
                })
            
            # 4. Burn subtitles
            if adjusted_subtitles:
                self.add_subtitles(
                    video_path=temp_pip,
                    output_path=output_path,
                    subtitles=adjusted_subtitles
                )
            else:
                # No subtitles, just copy
                import shutil
                shutil.copy(temp_pip, output_path)
            
            logger.info(f"Viral clip with PiP saved to: {output_path}")
            return output_path
            
        finally:
            if temp_trim.exists():
                temp_trim.unlink()
            if temp_pip.exists():
                temp_pip.unlink()
    
    def _resize_to_vertical(
        self,
        input_path: Path,
        output_path: Path,
        fps: int = 60
    ) -> Path:
        """Resize video to 9:16 vertical format with center crop"""
        from moviepy import VideoFileClip
        
        clip = VideoFileClip(str(input_path))
        
        target_w = 1080
        target_h = 1920
        
        # Scale to cover
        scale_w = target_w / clip.w
        scale_h = target_h / clip.h
        scale = max(scale_w, scale_h)
        
        resized = clip.resized(scale)
        cropped = resized.cropped(
            x_center=resized.w / 2,
            y_center=resized.h / 2,
            width=target_w,
            height=target_h
        )
        
        cropped.write_videofile(
            str(output_path),
            fps=fps,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=str(output_path.with_suffix(".m4a")),
            remove_temp=True,
            logger=None,
            preset="medium",
            bitrate="8000k"
        )
        
        clip.close()
        cropped.close()
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
