# Services package
from .transcriber import transcription_service, TranscriptionService
from .clipper import clip_finder_service, ClipFinderService
from .resizer import resize_service, ResizeService
from .editor import video_editor_service, VideoEditorService
from .description import description_service, DescriptionGeneratorService
from .effects import effects_service, EffectsService
from .youtube import youtube_service, YouTubeService
from .facecam import facecam_detector, FacecamDetector
from .captions import captions_service, CaptionsService, CaptionStyle, CAPTION_THEMES

# New AI-Video-Transcriber inspired services
from .summarizer import summarizer_service, SummarizerService
from .translator import translator_service, TranslatorService
from .video_downloader import video_downloader_service, VideoDownloaderService
from .exporter import (
    export_to_markdown,
    export_to_srt,
    export_to_vtt,
    export_to_json,
)

# Enhanced Services (NEW)
from .enhanced_clipper import enhanced_clip_finder_service
from .enhanced_captions import enhanced_captions_service
from .scene_detection import scene_detection_service
from .camera_switching import camera_switching_service
from .optimized_processor import optimized_video_processor
from .batch_processor import batch_processing_service
from .quality_presets import quality_presets_service, QUALITY_PRESETS, QualityPreset

__all__ = [
    # Existing services
    "transcription_service",
    "TranscriptionService",
    "clip_finder_service",
    "ClipFinderService",
    "resize_service",
    "ResizeService",
    "video_editor_service",
    "VideoEditorService",
    "description_service",
    "DescriptionGeneratorService",
    "effects_service",
    "EffectsService",
    "youtube_service",
    "YouTubeService",
    "facecam_detector",
    "FacecamDetector",
    # Captions service
    "captions_service",
    "CaptionsService",
    "CaptionStyle",
    "CAPTION_THEMES",
    # New AI-Video-Transcriber services
    "summarizer_service",
    "SummarizerService",
    "translator_service",
    "TranslatorService",
    "video_downloader_service",
    "VideoDownloaderService",
    "export_to_markdown",
    "export_to_srt",
    "export_to_vtt",
    "export_to_json",
    # Enhanced Services
    "enhanced_clip_finder_service",
    "enhanced_captions_service",
    "scene_detection_service",
    "camera_switching_service",
    "optimized_video_processor",
    "batch_processing_service",
    "quality_presets_service",
    "QUALITY_PRESETS",
    "QualityPreset",
]
