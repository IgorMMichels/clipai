"""
ClipAI Backend - FastAPI Application
AI-powered video clipping tool with transcription, summarization, and translation
Enhanced with AI-Video-Transcriber features
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging

from config import settings
from api.routes import upload_router, clips_router, storage_router, transcribe_router


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Starting ClipAI Backend...")
    
    # Ensure directories exist
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # NOTE: We no longer auto-cleanup on startup to preserve user files
    # Users can manually clear storage via the Storage Manager UI
    
    logger.info(f"Upload directory: {settings.UPLOAD_DIR}")
    logger.info(f"Output directory: {settings.OUTPUT_DIR}")
    yield
    logger.info("Shutting down ClipAI Backend...")


# Create FastAPI app
app = FastAPI(
    title="ClipAI",
    description="""AI-powered video clipping tool. Transform long videos into viral clips.

## Features
- **Video Transcription**: Accurate speech-to-text using Faster-Whisper
- **AI Text Optimization**: Automatic typo correction and intelligent paragraphing
- **Multi-Platform Support**: Download from YouTube, TikTok, Bilibili, Instagram, Twitter, and 30+ more
- **AI Summarization**: Generate intelligent summaries in multiple languages
- **Translation**: Translate transcripts between languages
- **Real-time Progress**: SSE streaming for live progress updates
- **Clip Detection**: Find viral-worthy moments with AI scoring

## Transcription API
Use `/api/transcribe/url` or `/api/transcribe/file` for standalone transcription.
""",
    version="1.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for outputs
app.mount("/outputs", StaticFiles(directory=str(settings.OUTPUT_DIR)), name="outputs")

# Include routers
app.include_router(upload_router, prefix="/api")
app.include_router(clips_router, prefix="/api")
app.include_router(storage_router, prefix="/api")
app.include_router(transcribe_router, prefix="/api")
# app.include_router(captions_router, prefix="/api")  # Disabled due to import issues


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "name": "ClipAI",
        "version": "1.1.0",
        "status": "running",
        "docs": "/docs",
        "features": {
            "transcription": "/api/transcribe",
            "clip_detection": "/api/upload",
            "export": "/api/clips",
        }
    }


@app.get("/api/health")
async def health():
    """Health check for API"""
    return {"status": "healthy"}


@app.get("/api/capabilities")
async def capabilities():
    """Get API capabilities and supported features"""
    from services.video_downloader import video_downloader_service
    from services.summarizer import SUMMARY_LANGUAGES
    from services.translator import SUPPORTED_LANGUAGES
    from services.captions import CAPTION_THEMES, CaptionStyle
    
    return {
        "transcription": {
            "engine": "Faster-Whisper",
            "models": ["tiny", "base", "small", "medium", "large"],
            "features": [
                "Word-level timestamps",
                "VAD filtering",
                "AI text optimization",
                "Auto language detection",
            ],
        },
        "captions": {
            "themes": [
                {"id": theme_id, "name": theme.name}
                for theme_id, theme in CAPTION_THEMES.items()
            ],
            "styles": [style.value for style in CaptionStyle],
            "features": [
                "Karaoke-style word highlighting",
                "Gradient color transitions",
                "Bounce animations",
                "Neon glow effects",
            ],
        },
        "platforms": video_downloader_service.get_supported_platforms(),
        "summary_languages": [
            {"code": code, "name": name}
            for code, name in SUMMARY_LANGUAGES.items()
        ],
        "translation_languages": [
            {"code": code, "name": name}
            for code, name in SUPPORTED_LANGUAGES.items()
        ],
        "export_formats": ["markdown", "srt", "vtt", "json"],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
