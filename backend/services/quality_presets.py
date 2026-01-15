"""
Quality Presets Service
Pre-configured export settings for different platforms
"""
from typing import Dict, Tuple
from dataclasses import dataclass


@dataclass
class QualityPreset:
    """Quality preset configuration"""
    name: str
    description: str
    resolution: Tuple[int, int]  # (width, height)
    fps: int
    video_bitrate: str
    audio_bitrate: str
    preset: str  # FFmpeg preset
    crf: int  # Constant Rate Factor (0-51, lower = better)
    codec: str = "libx264"
    audio_codec: str = "aac"


# Quality presets for different platforms
QUALITY_PRESETS: Dict[str, QualityPreset] = {
    "tiktok": QualityPreset(
        name="TikTok",
        description="Optimized for TikTok (9:16, 60fps)",
        resolution=(1080, 1920),
        fps=60,
        video_bitrate="8000k",
        audio_bitrate="192k",
        preset="fast",
        crf=20,
    ),
    "instagram_reels": QualityPreset(
        name="Instagram Reels",
        description="Optimized for Instagram Reels (9:16, 60fps)",
        resolution=(1080, 1920),
        fps=60,
        video_bitrate="8000k",
        audio_bitrate="192k",
        preset="fast",
        crf=20,
    ),
    "youtube_shorts": QualityPreset(
        name="YouTube Shorts",
        description="Optimized for YouTube Shorts (9:16, 60fps)",
        resolution=(1080, 1920),
        fps=60,
        video_bitrate="8000k",
        audio_bitrate="192k",
        preset="fast",
        crf=20,
    ),
    "youtube_standard": QualityPreset(
        name="YouTube Standard",
        description="Standard YouTube (16:9, 30fps)",
        resolution=(1920, 1080),
        fps=30,
        video_bitrate="5000k",
        audio_bitrate="192k",
        preset="medium",
        crf=18,
    ),
    "twitter": QualityPreset(
        name="Twitter/X",
        description="Optimized for Twitter (16:9, 30fps)",
        resolution=(1280, 720),
        fps=30,
        video_bitrate="3000k",
        audio_bitrate="128k",
        preset="fast",
        crf=22,
    ),
    "linkedin": QualityPreset(
        name="LinkedIn",
        description="Optimized for LinkedIn (16:9, 30fps)",
        resolution=(1280, 720),
        fps=30,
        video_bitrate="3000k",
        audio_bitrate="128k",
        preset="fast",
        crf=22,
    ),
    "facebook": QualityPreset(
        name="Facebook",
        description="Optimized for Facebook (16:9, 30fps)",
        resolution=(1920, 1080),
        fps=30,
        video_bitrate="4000k",
        audio_bitrate="192k",
        preset="medium",
        crf=20,
    ),
    "high_quality": QualityPreset(
        name="High Quality",
        description="Best quality (1080p, 60fps)",
        resolution=(1920, 1080),
        fps=60,
        video_bitrate="10000k",
        audio_bitrate="192k",
        preset="slow",
        crf=16,
    ),
    "balanced": QualityPreset(
        name="Balanced",
        description="Balanced quality and size (720p, 30fps)",
        resolution=(1280, 720),
        fps=30,
        video_bitrate="3000k",
        audio_bitrate="128k",
        preset="medium",
        crf=20,
    ),
    "fast": QualityPreset(
        name="Fast Export",
        description="Fast processing (720p, 30fps)",
        resolution=(1280, 720),
        fps=30,
        video_bitrate="2500k",
        audio_bitrate="128k",
        preset="veryfast",
        crf=24,
    ),
}


class QualityPresetsService:
    """Service for managing quality presets"""

    def get_all_presets(self) -> Dict[str, QualityPreset]:
        """Get all available quality presets"""
        return QUALITY_PRESETS

    def get_preset(self, preset_id: str) -> QualityPreset:
        """Get a specific quality preset"""
        return QUALITY_PRESETS.get(preset_id, QUALITY_PRESETS["balanced"])

    def get_recommended_presets(self, platform: str) -> List[str]:
        """Get recommended presets for a specific platform"""
        recommendations = {
            "tiktok": ["tiktok", "instagram_reels"],
            "instagram": ["instagram_reels", "facebook"],
            "youtube": ["youtube_shorts", "youtube_standard", "high_quality"],
            "twitter": ["twitter", "balanced"],
            "linkedin": ["linkedin", "balanced"],
            "facebook": ["facebook", "high_quality"],
        }
        return recommendations.get(platform, ["balanced"])

    def get_preset_for_aspect_ratio(
        self,
        aspect_ratio: Tuple[int, int],
        fps: int = 30,
    ) -> QualityPreset:
        """Get appropriate preset for aspect ratio and FPS"""
        w, h = aspect_ratio

        # Vertical videos
        if h > w:
            if fps >= 60:
                return QUALITY_PRESETS["tiktok"]
            else:
                return QUALITY_PRESETS["instagram_reels"]

        # Horizontal videos
        else:
            if fps >= 60:
                return QUALITY_PRESETS["high_quality"]
            else:
                return QUALITY_PRESETS["balanced"]

    def get_ffmpeg_args_from_preset(
        self,
        preset: QualityPreset,
    ) -> Dict[str, any]:
        """Convert preset to FFmpeg arguments"""
        return {
            "resolution": f"{preset.resolution[0]}x{preset.resolution[1]}",
            "fps": str(preset.fps),
            "video_bitrate": preset.video_bitrate,
            "audio_bitrate": preset.audio_bitrate,
            "preset": preset.preset,
            "crf": str(preset.crf),
            "codec": preset.codec,
            "audio_codec": preset.audio_codec,
        }


# Singleton instance
quality_presets_service = QualityPresetsService()
