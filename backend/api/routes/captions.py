"""
Captions API Routes
Endpoints for generating and burning AI-powered captions
"""
import logging
import uuid
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from services.captions import captions_service, CaptionStyle, CAPTION_THEMES
from services.transcriber import transcription_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/captions", tags=["captions"])

# Storage paths
STORAGE_DIR = Path("storage")
CAPTIONS_DIR = STORAGE_DIR / "captions"
CAPTIONS_DIR.mkdir(parents=True, exist_ok=True)


class WordTimestamp(BaseModel):
    """Word with timestamp"""
    text: str
    start_time: float
    end_time: float


class GenerateCaptionsRequest(BaseModel):
    """Request to generate caption file"""
    words: List[WordTimestamp] = Field(..., description="Words with timestamps")
    theme_id: str = Field(default="viral", description="Caption theme ID")
    style: str = Field(default="karaoke", description="Caption style: karaoke, gradient, bounce, viral")
    width: int = Field(default=1080, description="Video width")
    height: int = Field(default=1920, description="Video height")
    words_per_line: int = Field(default=3, ge=1, le=10, description="Words per caption line")
    time_offset: float = Field(default=0.0, description="Time offset in seconds")


class BurnCaptionsRequest(BaseModel):
    """Request to burn captions onto a video"""
    video_path: str = Field(..., description="Path to input video")
    words: List[WordTimestamp] = Field(..., description="Words with timestamps")
    theme_id: str = Field(default="viral", description="Caption theme ID")
    style: str = Field(default="karaoke", description="Caption style")
    words_per_line: int = Field(default=3, ge=1, le=10, description="Words per caption line")
    time_offset: float = Field(default=0.0, description="Time offset in seconds")
    output_filename: Optional[str] = Field(default=None, description="Output filename (optional)")


class TranscribeAndCaptionRequest(BaseModel):
    """Request to transcribe video and generate captions"""
    video_path: str = Field(..., description="Path to video file")
    theme_id: str = Field(default="viral", description="Caption theme ID")
    style: str = Field(default="karaoke", description="Caption style")
    words_per_line: int = Field(default=3, description="Words per caption line")
    language: Optional[str] = Field(default=None, description="Language code (auto-detect if None)")
    burn_to_video: bool = Field(default=False, description="Burn captions directly to video")


class CaptionThemeResponse(BaseModel):
    """Caption theme info"""
    id: str
    name: str


class GenerateCaptionsResponse(BaseModel):
    """Response with generated caption file"""
    success: bool
    ass_path: str
    message: str


class BurnCaptionsResponse(BaseModel):
    """Response with captioned video"""
    success: bool
    video_path: str
    message: str


@router.get("/themes", response_model=List[CaptionThemeResponse])
async def get_caption_themes():
    """Get available caption themes"""
    return [
        CaptionThemeResponse(id=theme_id, name=theme.name)
        for theme_id, theme in CAPTION_THEMES.items()
    ]


@router.get("/styles")
async def get_caption_styles():
    """Get available caption styles"""
    return [
        {"id": style.value, "name": style.name.title(), "description": desc}
        for style, desc in [
            (CaptionStyle.KARAOKE, "Word-by-word highlighting as each word is spoken"),
            (CaptionStyle.GRADIENT, "Colorful gradient transitions between lines"),
            (CaptionStyle.BOUNCE, "Bouncy animation on each word"),
            (CaptionStyle.VIRAL, "Classic viral style with subtle pop animation"),
            (CaptionStyle.MINIMAL, "Clean, minimal style for professional content"),
            (CaptionStyle.NEON, "Neon glow effect for gaming/music content"),
        ]
    ]


@router.post("/generate", response_model=GenerateCaptionsResponse)
async def generate_captions(request: GenerateCaptionsRequest):
    """
    Generate an ASS caption file from word timestamps
    
    Returns the path to the generated ASS file that can be used with FFmpeg
    """
    try:
        # Convert words to dict format
        words = [w.model_dump() for w in request.words]
        
        # Parse style
        try:
            style = CaptionStyle(request.style.lower())
        except ValueError:
            style = CaptionStyle.KARAOKE
        
        # Generate unique filename
        caption_id = str(uuid.uuid4())[:8]
        output_path = CAPTIONS_DIR / f"captions_{caption_id}.ass"
        
        # Generate ASS file
        result_path = captions_service.generate_captions_ass(
            words=words,
            output_path=output_path,
            theme_id=request.theme_id,
            style=style,
            width=request.width,
            height=request.height,
            words_per_line=request.words_per_line,
            time_offset=request.time_offset,
        )
        
        return GenerateCaptionsResponse(
            success=True,
            ass_path=str(result_path),
            message=f"Generated captions with {len(words)} words using {request.theme_id} theme"
        )
        
    except Exception as e:
        logger.error(f"Failed to generate captions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/burn", response_model=BurnCaptionsResponse)
async def burn_captions(request: BurnCaptionsRequest):
    """
    Burn captions directly onto a video file
    
    Takes a video and word timestamps, generates styled captions,
    and burns them into the video.
    """
    try:
        video_path = Path(request.video_path)
        if not video_path.exists():
            raise HTTPException(status_code=404, detail=f"Video not found: {video_path}")
        
        # Convert words to dict format
        words = [w.model_dump() for w in request.words]
        
        # Parse style
        try:
            style = CaptionStyle(request.style.lower())
        except ValueError:
            style = CaptionStyle.KARAOKE
        
        # Generate output path
        if request.output_filename:
            output_path = video_path.parent / request.output_filename
        else:
            output_path = video_path.parent / f"{video_path.stem}_captioned{video_path.suffix}"
        
        # Burn captions
        result_path = captions_service.burn_captions_to_video(
            video_path=video_path,
            output_path=output_path,
            words=words,
            theme_id=request.theme_id,
            style=style,
            words_per_line=request.words_per_line,
            time_offset=request.time_offset,
        )
        
        return BurnCaptionsResponse(
            success=True,
            video_path=str(result_path),
            message=f"Burned {len(words)} words onto video with {request.theme_id} theme"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to burn captions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transcribe-and-caption")
async def transcribe_and_caption(request: TranscribeAndCaptionRequest):
    """
    Full pipeline: Transcribe video and generate/burn captions
    
    1. Transcribes the video to get word-level timestamps
    2. Generates styled captions
    3. Optionally burns captions onto the video
    """
    try:
        video_path = Path(request.video_path)
        if not video_path.exists():
            raise HTTPException(status_code=404, detail=f"Video not found: {video_path}")
        
        # Step 1: Transcribe
        logger.info(f"Transcribing video: {video_path}")
        transcription = transcription_service.transcribe(
            file_path=video_path,
            language=request.language,
            optimize_with_ai=False  # Skip AI optimization for speed
        )
        
        words = transcription.get("words", [])
        if not words:
            raise HTTPException(status_code=400, detail="No words detected in transcription")
        
        logger.info(f"Transcribed {len(words)} words")
        
        # Parse style
        try:
            style = CaptionStyle(request.style.lower())
        except ValueError:
            style = CaptionStyle.KARAOKE
        
        # Step 2: Generate or burn captions
        if request.burn_to_video:
            output_path = video_path.parent / f"{video_path.stem}_captioned{video_path.suffix}"
            
            result_path = captions_service.burn_captions_to_video(
                video_path=video_path,
                output_path=output_path,
                words=words,
                theme_id=request.theme_id,
                style=style,
                words_per_line=request.words_per_line,
            )
            
            return {
                "success": True,
                "video_path": str(result_path),
                "words_count": len(words),
                "language": transcription.get("language", "en"),
                "message": f"Transcribed and burned captions to video"
            }
        else:
            # Just generate ASS file
            caption_id = str(uuid.uuid4())[:8]
            output_path = CAPTIONS_DIR / f"captions_{caption_id}.ass"
            
            # Get video dimensions
            width, height = captions_service._get_video_dimensions(video_path)
            
            result_path = captions_service.generate_captions_ass(
                words=words,
                output_path=output_path,
                theme_id=request.theme_id,
                style=style,
                width=width,
                height=height,
                words_per_line=request.words_per_line,
            )
            
            return {
                "success": True,
                "ass_path": str(result_path),
                "words": words,
                "words_count": len(words),
                "language": transcription.get("language", "en"),
                "text": transcription.get("text", ""),
                "message": f"Transcribed video and generated captions"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to transcribe and caption: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preview-styles")
async def preview_caption_styles():
    """
    Get preview data for all caption styles
    
    Returns sample ASS content for each style that can be used for previews
    """
    sample_words = [
        {"text": "This", "start_time": 0.0, "end_time": 0.3},
        {"text": "is", "start_time": 0.3, "end_time": 0.5},
        {"text": "a", "start_time": 0.5, "end_time": 0.6},
        {"text": "sample", "start_time": 0.6, "end_time": 1.0},
        {"text": "caption", "start_time": 1.0, "end_time": 1.5},
        {"text": "preview", "start_time": 1.5, "end_time": 2.0},
    ]
    
    previews = []
    for style in [CaptionStyle.KARAOKE, CaptionStyle.GRADIENT, CaptionStyle.BOUNCE, CaptionStyle.VIRAL]:
        for theme_id in ["viral", "gradient_sunset", "neon_pink"]:
            previews.append({
                "style": style.value,
                "theme": theme_id,
                "theme_name": CAPTION_THEMES[theme_id].name,
                "sample_words": sample_words,
            })
    
    return previews
