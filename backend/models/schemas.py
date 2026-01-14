from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DOWNLOADING = "downloading"
    TRANSCRIBING = "transcribing"
    FINDING_CLIPS = "finding_clips"
    RESIZING = "resizing"
    GENERATING_DESCRIPTION = "generating_description"
    ADDING_EFFECTS = "adding_effects"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoUploadRequest(BaseModel):
    language: Optional[str] = None  # Auto-detect if None
    aspect_ratio: tuple[int, int] = (9, 16)
    generate_description: bool = True
    description_language: str = "en"  # "en" or "pt"


class YouTubeUploadRequest(BaseModel):
    url: str
    language: Optional[str] = None
    aspect_ratio: tuple[int, int] = (9, 16)
    generate_description: bool = True
    description_language: str = "en"


class ClipInfo(BaseModel):
    id: str
    start_time: float
    end_time: float
    duration: float
    transcript: str
    score: float = 0.0
    description: Optional[str] = None
    output_path: Optional[str] = None


class VideoJob(BaseModel):
    id: str
    filename: str
    original_path: str
    status: ProcessingStatus = ProcessingStatus.PENDING
    progress: int = 0
    message: str = ""
    language: Optional[str] = None
    transcript: Optional[str] = None
    clips: List[ClipInfo] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class VideoJobResponse(BaseModel):
    id: str
    status: ProcessingStatus
    progress: int
    message: str
    clips_count: int = 0


class ClipExportRequest(BaseModel):
    clip_ids: List[str]
    aspect_ratio: tuple[int, int] = (9, 16)
    layout: str = "fill"  # "fill" or "stacked"
    add_music: bool = False
    music_track: Optional[str] = None
    add_subtitles: bool = True
    generate_description: bool = True
    description_language: str = "en"


class DescriptionRequest(BaseModel):
    transcript: str
    language: str = "en"  # "en" or "pt"
    style: str = "social_media"  # "social_media", "professional", "casual"
    max_length: int = 200


class DescriptionResponse(BaseModel):
    description: str
    hashtags: List[str]
    language: str
