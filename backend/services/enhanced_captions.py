"""
Enhanced AI Captions Service
Advanced caption generation with smart positioning, timing, and visual optimization
"""
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Literal
from dataclasses import dataclass
from enum import Enum
import subprocess
import tempfile
import os
import re
import numpy as np

logger = logging.getLogger(__name__)


class CaptionStyle(str, Enum):
    """Available caption styles"""
    VIRAL = "viral"           # Classic viral style - white bold with black outline
    KARAOKE = "karaoke"       # Word-by-word highlighting
    GRADIENT = "gradient"     # Colorful gradient animated
    MINIMAL = "minimal"       # Clean, minimal style
    NEON = "neon"            # Neon glow effect
    BOUNCE = "bounce"        # Bouncy animated text
    WAVE = "wave"            # Wave animation effect
    GLOW = "glow"            # Glowing text effect


@dataclass
class CaptionPosition:
    """Smart caption positioning"""
    margin_v: int = 150           # Distance from bottom (default)
    margin_h: int = 20            # Horizontal margin
    alignment: int = 2            # Bottom center
    avoid_center: bool = False      # Avoid center area for gameplay


@dataclass
class CaptionTheme:
    """Theme configuration for captions"""
    name: str
    font_name: str = "Arial Black"
    font_size: int = 80
    primary_color: str = "&H00FFFFFF"    # White (ASS BGR format)
    secondary_color: str = "&H0000FFFF"  # Yellow highlight
    outline_color: str = "&H00000000"    # Black outline
    back_color: str = "&H80000000"       # Semi-transparent shadow
    outline_width: int = 4
    shadow_depth: int = 2
    bold: bool = True
    position: CaptionPosition = None
    animation: Optional[str] = None      # ASS animation effects


# Predefined themes with smart positioning
CAPTION_THEMES: Dict[str, CaptionTheme] = {
    "viral": CaptionTheme(
        name="Viral",
        font_name="Arial Black",
        font_size=85,
        primary_color="&H00FFFFFF",
        secondary_color="&H0000FFFF",
        outline_color="&H00000000",
        outline_width=5,
        shadow_depth=3,
        bold=True,
        position=CaptionPosition(margin_v=150, margin_h=20, alignment=2, avoid_center=False),
    ),
    "gradient_sunset": CaptionTheme(
        name="Gradient Sunset",
        font_name="Impact",
        font_size=90,
        primary_color="&H004080FF",      # Orange-ish
        secondary_color="&H00FF40FF",    # Pink/Magenta
        outline_color="&H00000000",
        outline_width=4,
        shadow_depth=2,
        bold=True,
        animation="gradient",
        position=CaptionPosition(margin_v=140, avoid_center=False),
    ),
    "gradient_ocean": CaptionTheme(
        name="Gradient Ocean",
        font_name="Impact",
        font_size=90,
        primary_color="&H00FFFF00",      # Cyan
        secondary_color="&H00FF8000",    # Blue
        outline_color="&H00000000",
        outline_width=4,
        shadow_depth=2,
        bold=True,
        animation="gradient",
        position=CaptionPosition(margin_v=140, avoid_center=False),
    ),
    "neon_pink": CaptionTheme(
        name="Neon Pink",
        font_name="Arial Black",
        font_size=80,
        primary_color="&H00FF00FF",      # Magenta
        secondary_color="&H00FFFFFF",
        outline_color="&H00800080",      # Purple glow
        back_color="&H40FF00FF",
        outline_width=6,
        shadow_depth=4,
        bold=True,
        animation="glow",
    ),
    "neon_blue": CaptionTheme(
        name="Neon Blue",
        font_name="Arial Black",
        font_size=80,
        primary_color="&H00FFFF00",      # Cyan
        secondary_color="&H00FFFFFF",
        outline_color="&H00FF8000",      # Blue glow
        back_color="&H40FFFF00",
        outline_width=6,
        shadow_depth=4,
        bold=True,
        animation="glow",
    ),
    "minimal": CaptionTheme(
        name="Minimal",
        font_name="Helvetica",
        font_size=65,
        primary_color="&H00FFFFFF",
        outline_color="&H00000000",
        outline_width=2,
        shadow_depth=0,
        bold=False,
    ),
    "bounce": CaptionTheme(
        name="Bounce",
        font_name="Arial Black",
        font_size=85,
        primary_color="&H0000FFFF",      # Yellow
        secondary_color="&H00FFFFFF",
        outline_color="&H00000000",
        outline_width=5,
        shadow_depth=2,
        bold=True,
        animation="bounce",
    ),
    "wave": CaptionTheme(
        name="Wave",
        font_name="Arial Black",
        font_size=80,
        primary_color="&H00FFFFFF",
        secondary_color="&H0000FFFF",
        outline_color="&H00000000",
        outline_width=4,
        shadow_depth=2,
        bold=True,
        animation="wave",
        position=CaptionPosition(margin_v=160, avoid_center=False),
    ),
}


class EnhancedCaptionsService:
    """Service for generating beautiful AI-powered captions with smart features"""

    def __init__(self):
        self.default_theme = "viral"

    def get_available_themes(self) -> List[Dict[str, str]]:
        """Get list of available caption themes"""
        return [
            {"id": key, "name": theme.name}
            for key, theme in CAPTION_THEMES.items()
        ]

    def generate_captions_ass(
        self,
        words: List[Dict[str, Any]],
        output_path: Path,
        theme_id: str = "viral",
        style: CaptionStyle = CaptionStyle.KARAOKE,
        width: int = 1080,
        height: int = 1920,
        words_per_line: int = 3,
        time_offset: float = 0.0,
        smart_positioning: bool = True,
        optimize_timing: bool = True,
    ) -> Path:
        """
        Generate ASS subtitle file with beautiful styled captions

        Args:
            words: List of word dicts with 'text', 'start_time', 'end_time'
            output_path: Path for output ASS file
            theme_id: Theme identifier (viral, gradient_sunset, neon_pink, etc.)
            style: Caption style (karaoke, viral, gradient, etc.)
            width: Video width
            height: Video height
            words_per_line: Number of words to show per caption line
            time_offset: Time offset to apply to all timestamps
            smart_positioning: Use smart positioning to avoid important content
            optimize_timing: Optimize caption timing based on speech pace

        Returns:
            Path to generated ASS file
        """
        theme = CAPTION_THEMES.get(theme_id, CAPTION_THEMES[self.default_theme])

        # Scale font size and positioning based on resolution
        scale_factor = height / 1920
        font_size = int(theme.font_size * scale_factor)

        if theme.position:
            position = theme.position
            margin_v = int(position.margin_v * scale_factor)
        else:
            margin_v = int(150 * scale_factor)

        outline = max(2, int(theme.outline_width * scale_factor))
        shadow = max(1, int(theme.shadow_depth * scale_factor))

        # Optimize words per line based on screen width
        optimal_words_per_line = self._calculate_optimal_words_per_line(
            words, width, font_size
        )

        # Generate based on style
        if style == CaptionStyle.KARAOKE:
            content = self._generate_karaoke_ass(
                words, theme, font_size, margin_v, outline, shadow,
                width, height, optimal_words_per_line, time_offset
            )
        elif style == CaptionStyle.GRADIENT:
            content = self._generate_gradient_ass(
                words, theme, font_size, margin_v, outline, shadow,
                width, height, optimal_words_per_line, time_offset
            )
        elif style == CaptionStyle.BOUNCE:
            content = self._generate_bounce_ass(
                words, theme, font_size, margin_v, outline, shadow,
                width, height, optimal_words_per_line, time_offset
            )
        elif style == CaptionStyle.WAVE:
            content = self._generate_wave_ass(
                words, theme, font_size, margin_v, outline, shadow,
                width, height, optimal_words_per_line, time_offset
            )
        elif style == CaptionStyle.GLOW:
            content = self._generate_glow_ass(
                words, theme, font_size, margin_v, outline, shadow,
                width, height, optimal_words_per_line, time_offset
            )
        else:
            # Default to viral style
            content = self._generate_viral_ass(
                words, theme, font_size, margin_v, outline, shadow,
                width, height, optimal_words_per_line, time_offset
            )

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Generated enhanced ASS captions: {output_path}")
        return output_path

    def _calculate_optimal_words_per_line(
        self,
        words: List[Dict[str, Any]],
        width: int,
        font_size: int,
    ) -> int:
        """
        Calculate optimal words per line based on average word length
        """
        if not words:
            return 3

        avg_word_length = np.mean([len(w.get("text", "")) for w in words])

        # Estimate character width (rough approximation)
        char_width = font_size * 0.6

        # Calculate max chars that fit
        max_chars = (width - 40) / char_width  # 40px padding

        # Calculate optimal words
        optimal_words = int(max_chars / (avg_word_length + 1))  # +1 for space

        return max(2, min(5, optimal_words))

    def _format_ass_time(self, seconds: float) -> str:
        """Format time for ASS format: H:MM:SS.cc"""
        seconds = max(0, seconds)
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centiseconds = int((seconds % 1) * 100)
        return f"{hours:d}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"

    def _get_ass_header(
        self,
        theme: CaptionTheme,
        font_size: int,
        margin_v: int,
        outline: int,
        shadow: int,
        width: int,
        height: int,
        extra_styles: str = ""
    ) -> str:
        """Generate ASS file header with styles"""
        bold = -1 if theme.bold else 0
        alignment = theme.position.alignment if theme.position else 2

        header = f"""[Script Info]
Title: ClipAI Enhanced Captions
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: {width}
PlayResY: {height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{theme.font_name},{font_size},{theme.primary_color},{theme.secondary_color},{theme.outline_color},{theme.back_color},{bold},0,0,0,100,100,0,0,1,{outline},{shadow},{alignment},20,20,{margin_v},1
Style: Highlight,{theme.font_name},{int(font_size * 1.1)},{theme.secondary_color},{theme.primary_color},{theme.outline_color},{theme.back_color},{-1 if theme.bold else 0},0,0,0,105,105,0,0,1,{outline},{shadow},{alignment},20,20,{margin_v},1
{extra_styles}
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        return header

    def _group_words_into_lines(
        self,
        words: List[Dict[str, Any]],
        words_per_line: int,
        time_offset: float
    ) -> List[Dict[str, Any]]:
        """Group words into caption lines with smart timing"""
        lines = []
        current_line_words = []

        for word in words:
            word_text = word.get("text", "").strip()
            if not word_text:
                continue

            current_line_words.append({
                "text": word_text,
                "start": word.get("start_time", 0) - time_offset,
                "end": word.get("end_time", 0) - time_offset,
            })

            # Check for sentence endings
            is_sentence_end = word_text.rstrip()[-1:] in ".!?" if word_text.rstrip() else False

            # Create new line
            if len(current_line_words) >= words_per_line or is_sentence_end:
                if current_line_words:
                    # Smart timing: extend line duration slightly for readability
                    line_start = current_line_words[0]["start"]
                    line_end = current_line_words[-1]["end"]
                    duration = line_end - line_start

                    # Add small buffer for readability
                    if duration > 0.5:
                        line_end += 0.1

                    lines.append({
                        "words": current_line_words,
                        "start": line_start,
                        "end": line_end,
                        "text": " ".join(w["text"] for w in current_line_words)
                    })
                    current_line_words = []

        # Add remaining words
        if current_line_words:
            line_start = current_line_words[0]["start"]
            line_end = current_line_words[-1]["end"]
            lines.append({
                "words": current_line_words,
                "start": line_start,
                "end": line_end,
                "text": " ".join(w["text"] for w in current_line_words)
            })

        return lines

    def _generate_karaoke_ass(
        self,
        words: List[Dict[str, Any]],
        theme: CaptionTheme,
        font_size: int,
        margin_v: int,
        outline: int,
        shadow: int,
        width: int,
        height: int,
        words_per_line: int,
        time_offset: float
    ) -> str:
        """Generate karaoke-style ASS with word-by-word highlighting"""

        # Create extra style for active word
        extra_styles = f"""Style: Active,{theme.font_name},{int(font_size * 1.1)},{theme.secondary_color},{theme.primary_color},{theme.outline_color},{theme.back_color},{-1 if theme.bold else 0},0,0,0,105,105,0,0,1,{outline},{shadow},{theme.position.alignment if theme.position else 2},20,20,{margin_v},1
"""

        content = self._get_ass_header(
            theme, font_size, margin_v, outline, shadow, width, height, extra_styles
        )

        lines = self._group_words_into_lines(words, words_per_line, time_offset)

        for line in lines:
            line_start = line["start"]
            line_end = line["end"]

            if line_end <= 0:
                continue

            line_words = line["words"]

            # For each word, create a dialogue line
            for i, word in enumerate(line_words):
                word_start = max(0, word["start"])
                word_end = word["end"]

                if word_end <= 0:
                    continue

                # Build text with current word highlighted
                text_parts = []
                for j, w in enumerate(line_words):
                    word_upper = w["text"].upper()
                    if j == i:
                        # Highlight current word with color and scale
                        text_parts.append(f"{{\\c{theme.secondary_color}\\fscx110\\fscy110}}{word_upper}{{\\c{theme.primary_color}\\fscx100\\fscy100}}")
                    else:
                        text_parts.append(word_upper)

                full_text = " ".join(text_parts)

                start_str = self._format_ass_time(word_start)
                end_str = self._format_ass_time(word_end)

                content += f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{full_text}\n"

        return content

    def _generate_glow_ass(
        self,
        words: List[Dict[str, Any]],
        theme: CaptionTheme,
        font_size: int,
        margin_v: int,
        outline: int,
        shadow: int,
        width: int,
        height: int,
        words_per_line: int,
        time_offset: float
    ) -> str:
        """Generate glow-style ASS with neon effect"""

        # Create glow style
        extra_styles = f"""Style: Glow,{theme.font_name},{font_size},{theme.back_color},{theme.primary_color},{theme.outline_color},&H40000000,{-1 if theme.bold else 0},0,0,0,100,100,0,0,3,{outline},{shadow},{theme.position.alignment if theme.position else 2},20,20,{margin_v},1
"""

        content = self._get_ass_header(
            theme, font_size, margin_v, outline, shadow, width, height, extra_styles
        )

        lines = self._group_words_into_lines(words, words_per_line, time_offset)

        for line in lines:
            line_start = max(0, line["start"])
            line_end = line["end"]

            if line_end <= 0:
                continue

            text_upper = line["text"].upper()

            # Add glow effect with blur
            glow_text = f"{{\\blur2}}{text_upper}{{\\blur0}}"
            start_str = self._format_ass_time(line_start)
            end_str = self._format_ass_time(line_end)

            # First layer: glow
            content += f"Dialogue: 1,{start_str},{end_str},Glow,,0,0,0,,{glow_text}\n"
            # Second layer: main text
            content += f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text_upper}\n"

        return content

    def _generate_wave_ass(
        self,
        words: List[Dict[str, Any]],
        theme: CaptionTheme,
        font_size: int,
        margin_v: int,
        outline: int,
        shadow: int,
        width: int,
        height: int,
        words_per_line: int,
        time_offset: float
    ) -> str:
        """Generate wave-style ASS with animated wave effect"""

        content = self._get_ass_header(
            theme, font_size, margin_v, outline, shadow, width, height
        )

        lines = self._group_words_into_lines(words, words_per_line, time_offset)

        for line in lines:
            line_start = max(0, line["start"])
            line_end = line["end"]

            if line_end <= 0:
                continue

            text_upper = line["text"].upper()

            # Wave effect using position animation
            wave_text = f"{{\\t(0,{int(line['end']*1000)},\\frx30\\frz10)}}{text_upper}"

            start_str = self._format_ass_time(line_start)
            end_str = self._format_ass_time(line_end)

            content += f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{wave_text}\n"

        return content

    def _generate_gradient_ass(
        self,
        words: List[Dict[str, Any]],
        theme: CaptionTheme,
        font_size: int,
        margin_v: int,
        outline: int,
        shadow: int,
        width: int,
        height: int,
        words_per_line: int,
        time_offset: float
    ) -> str:
        """Generate gradient-style ASS with colorful transitions"""

        colors = [
            "&H00FF6B9D",  # Pink
            "&H00C850C0",  # Purple
            "&H00FFDE59",  # Yellow
            "&H0059FFDE",  # Cyan
            "&H006BFF9D",  # Green
        ]

        content = self._get_ass_header(
            theme, font_size, margin_v, outline, shadow, width, height
        )

        lines = self._group_words_into_lines(words, words_per_line, time_offset)
        color_index = 0

        for line in lines:
            line_start = max(0, line["start"])
            line_end = line["end"]

            if line_end <= 0:
                continue

            line_words = line["words"]
            duration = line_end - line_start

            # Create gradient effect by animating between colors
            current_color = colors[color_index % len(colors)]
            next_color = colors[(color_index + 1) % len(colors)]

            # Use transition animation
            fade_effect = f"{{\\t(0,{int(duration * 500)},\\c{next_color})\\c{current_color}}}"
            scale_effect = "{{\\t(0,100,\\fscx105\\fscy105)\\t(100,200,\\fscx100\\fscy100)}}"

            full_text = f"{fade_effect}{scale_effect}{line['text'].upper()}"

            start_str = self._format_ass_time(line_start)
            end_str = self._format_ass_time(line_end)

            content += f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{full_text}\n"
            color_index += 1

        return content

    def _generate_bounce_ass(
        self,
        words: List[Dict[str, Any]],
        theme: CaptionTheme,
        font_size: int,
        margin_v: int,
        outline: int,
        shadow: int,
        width: int,
        height: int,
        words_per_line: int,
        time_offset: float
    ) -> str:
        """Generate bounce-style ASS with bouncy word animations"""

        content = self._get_ass_header(
            theme, font_size, margin_v, outline, shadow, width, height
        )

        lines = self._group_words_into_lines(words, words_per_line, time_offset)

        for line in lines:
            line_start = max(0, line["start"])
            line_end = line["end"]

            if line_end <= 0:
                continue

            line_words = line["words"]

            # Create bounce effect for each word
            for i, word in enumerate(line_words):
                word_start = max(0, word["start"])
                word_end = word["end"]
                word_duration = (word_end - word_start) * 1000  # in ms

                if word_end <= 0:
                    continue

                # Build text with current word having bounce effect
                text_parts = []
                for j, w in enumerate(line_words):
                    word_upper = w["text"].upper()
                    if j == i:
                        # Bounce animation: scale up then down
                        bounce_ms = min(150, int(word_duration / 3))
                        bounce_effect = (
                            f"{{\\t(0,{bounce_ms},\\fscx120\\fscy120)"
                            f"\\t({bounce_ms},{bounce_ms * 2},\\fscx100\\fscy100)"
                            f"\\c{theme.secondary_color}}}"
                        )
                        text_parts.append(f"{bounce_effect}{word_upper}{{\\c{theme.primary_color}}}")
                    else:
                        text_parts.append(word_upper)

                full_text = " ".join(text_parts)

                start_str = self._format_ass_time(word_start)
                end_str = self._format_ass_time(word_end)

                content += f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{full_text}\n"

        return content

    def _generate_viral_ass(
        self,
        words: List[Dict[str, Any]],
        theme: CaptionTheme,
        font_size: int,
        margin_v: int,
        outline: int,
        shadow: int,
        width: int,
        height: int,
        words_per_line: int,
        time_offset: float
    ) -> str:
        """Generate classic viral-style ASS captions"""

        content = self._get_ass_header(
            theme, font_size, margin_v, outline, shadow, width, height
        )

        lines = self._group_words_into_lines(words, words_per_line, time_offset)

        for line in lines:
            line_start = max(0, line["start"])
            line_end = line["end"]

            if line_end <= 0:
                continue

            text_upper = line["text"].upper()

            # Add subtle pop-in animation
            pop_effect = "{\\fad(50,50)\\t(0,50,\\fscx100\\fscy100)\\fscx95\\fscy95}"
            full_text = f"{pop_effect}{text_upper}"

            start_str = self._format_ass_time(line_start)
            end_str = self._format_ass_time(line_end)

            content += f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{full_text}\n"

        return content

    def burn_captions_to_video(
        self,
        video_path: Path,
        output_path: Path,
        words: List[Dict[str, Any]],
        theme_id: str = "viral",
        style: CaptionStyle = CaptionStyle.KARAOKE,
        words_per_line: int = 3,
        time_offset: float = 0.0,
        smart_positioning: bool = True,
    ) -> Path:
        """
        Burn styled captions directly onto a video

        Args:
            video_path: Input video path
            output_path: Output video path
            words: List of word dicts with timestamps
            theme_id: Caption theme to use
            style: Caption style (karaoke, gradient, etc.)
            words_per_line: Words per caption line
            time_offset: Time offset for subtitles
            smart_positioning: Use smart positioning to avoid important content

        Returns:
            Path to output video with burned captions
        """
        video_path = Path(video_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Get video dimensions
        width, height = self._get_video_dimensions(video_path)

        # Generate ASS file
        ass_path = output_path.with_suffix(".ass")
        self.generate_captions_ass(
            words=words,
            output_path=ass_path,
            theme_id=theme_id,
            style=style,
            width=width,
            height=height,
            words_per_line=words_per_line,
            time_offset=time_offset,
            smart_positioning=smart_positioning,
        )

        try:
            # Burn captions using FFmpeg
            ass_path_escaped = str(ass_path).replace("\\", "/").replace(":", "\\:")

            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-vf", f"ass='{ass_path_escaped}'",
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "18",
                "-c:a", "copy",
                str(output_path)
            ]

            logger.info(f"Burning enhanced captions to video: {output_path}")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise RuntimeError(f"Failed to burn captions: {result.stderr}")

            logger.info(f"Captions burned successfully: {output_path}")
            return output_path

        finally:
            # Cleanup ASS file
            if ass_path.exists():
                ass_path.unlink()

    def _get_video_dimensions(self, video_path: Path) -> tuple[int, int]:
        """Get video width and height using ffprobe"""
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "csv=p=0:s=x",
                str(video_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            width, height = map(int, result.stdout.strip().split("x"))
            return width, height
        except Exception as e:
            logger.warning(f"Could not get video dimensions: {e}, using default 1080x1920")
            return 1080, 1920

    def generate_from_transcription(
        self,
        transcription: Dict[str, Any],
        output_path: Path,
        theme_id: str = "viral",
        style: CaptionStyle = CaptionStyle.KARAOKE,
        width: int = 1080,
        height: int = 1920,
        words_per_line: int = 3,
        start_time: float = 0.0,
        end_time: Optional[float] = None,
    ) -> Path:
        """
        Generate captions from a transcription result

        Args:
            transcription: Transcription dict with 'words' list
            output_path: Output ASS file path
            theme_id: Caption theme
            style: Caption style
            width/height: Video dimensions
            words_per_line: Words per line
            start_time/end_time: Optional time range to filter words

        Returns:
            Path to generated ASS file
        """
        words = transcription.get("words", [])

        # Filter words by time range if specified
        if start_time > 0 or end_time is not None:
            filtered_words = []
            for word in words:
                word_start = word.get("start_time", 0)
                word_end = word.get("end_time", 0)

                if end_time is not None and word_start >= end_time:
                    break
                if word_end <= start_time:
                    continue

                filtered_words.append(word)
            words = filtered_words

        return self.generate_captions_ass(
            words=words,
            output_path=output_path,
            theme_id=theme_id,
            style=style,
            width=width,
            height=height,
            words_per_line=words_per_line,
            time_offset=start_time,
            smart_positioning=True,
            optimize_timing=True,
        )


# Singleton instance
enhanced_captions_service = EnhancedCaptionsService()
