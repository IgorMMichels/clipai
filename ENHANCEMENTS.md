# ClipAI - AI-Powered Video Clipping Platform

**Transform long videos into viral clips with AI analysis, smart camera switching, and beautiful captions.**

## 🚀 New Features (Enhanced Version)

### 🧠 Multi-Modal Virality Scoring
- **Semantic Analysis**: AI-powered content understanding using sentence transformers
- **Audio Energy**: Detect exciting moments through audio analysis
- **Visual Changes**: Track scene changes and motion dynamics
- **Weighted Scoring**: Combines semantic (40%), heuristic (25%), audio (20%), visual (15%)

### 🎥 Intelligent Scene Detection
- **Automatic Scene Cuts**: Detect scene boundaries with configurable thresholds
- **Transition Optimization**: Find optimal cutting points for smooth transitions
- **Scene Analysis**: Characterize scenes by brightness, contrast, color distribution

### 📸 Smart Camera Switching
- **Facecam Detection**: Identify facecam vs gameplay regions
- **Intelligent Switching**: Generate optimal switching points
- **Timeline Generation**: Create camera switching timelines synced with transcription

### 🎨 Enhanced Caption System
- **8 New Styles**: Viral, Karaoke, Gradient, Minimal, Neon, Bounce, Wave, Glow
- **Smart Positioning**: Automatic placement avoiding important content
- **Optimized Timing**: Adaptive timing based on speech pace
- **Better Visibility**: Enhanced font scaling and outline optimization

### ⚡ GPU Acceleration
- **Auto-Detection**: Automatically detect NVIDIA/Intel/macOS GPU
- **FFmpeg GPU**: CUDA, NVENC, QSV, VideoToolbox support
- **Optimized Presets**: Fast/medium/slow presets based on hardware
- **Performance**: 2-3x faster processing on supported hardware

### 📦 Batch Processing
- **Parallel Export**: Process multiple clips simultaneously
- **Progress Tracking**: Real-time progress for each clip
- **Configurable Workers**: Adjustable parallel processing (default: 3)
- **Smart Queuing**: Efficient task distribution

### 🎯 Quality Presets
- **Platform Optimized**: TikTok, Instagram Reels, YouTube Shorts, YouTube HD
- **Social Ready**: Twitter/X, LinkedIn, Facebook presets
- **Custom Options**: High Quality, Balanced, Fast Export presets
- **Auto-Selection**: Recommended presets per platform

---

## 📋 Original Features

### 🎬 Video Clipping (Core)
- **AI Clip Detection**: Finds engaging moments using semantic analysis
- **Smart Resizing**: Converts 16:9 to 9:16 with active speaker tracking
- **Facecam Detection**: Handles gaming/streaming video layouts
- **Viral Captions**: AI-generated descriptions and hashtags

### 📝 AI Transcriber
- **30+ Platforms**: Download from YouTube, TikTok, Instagram, Twitter, Bilibili, Vimeo, etc.
- **Faster-Whisper**: High-accuracy transcription with VAD filtering
- **AI Text Optimization**: Automatic typo correction and grammar fixes
- **Multi-Language**: Summaries in 20+ languages

---

## 🛠️ Tech Stack

- **Backend**: FastAPI, Python 3.11+
- **Frontend**: Next.js 16, React 19, TailwindCSS 4, shadcn/ui
- **AI/ML**:
  - Transcription: Faster-Whisper
  - LLMs: Google Gemini 2.0, OpenAI GPT-4o, Anthropic Claude
  - Embeddings: Sentence-Transformers
  - Vision: OpenCV, MediaPipe
- **Processing**: FFmpeg, MoviePy, yt-dlp
- **Optional**: CUDA, NVENC, QSV (Intel Quick Sync)

---

## ⚡ Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- FFmpeg (required)
- Optional: NVIDIA GPU, Intel Quick Sync

### Installation

1. **Clone and Setup**
   ```bash
   git clone https://github.com/yourusername/clipai.git
   cd clipai

   # Backend
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your API keys

   # Frontend
   cd ../frontend
   npm install
   npm run dev
   ```

2. **Run Backend**
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

3. **Access Application**
   - Frontend: `http://localhost:3000`
   - Backend API: `http://localhost:8000`
   - API Docs: `http://localhost:8000/docs`

---

## 🎯 Key Enhancements

### 1. Multi-Modal Clip Finding
**File**: `backend/services/enhanced_clipper.py`

New scoring algorithm combines:
- Semantic similarity to viral concepts (40% weight)
- Heuristic keyword analysis (25% weight)
- Audio energy peaks (20% weight)
- Visual change detection (15% weight)

### 2. Scene Detection
**File**: `backend/services/scene_detection.py`

Automatic scene boundary detection with:
- Frame difference analysis
- Configurable thresholds
- Minimum scene duration enforcement
- Scene characterization (brightness, contrast, color)

### 3. Camera Switching
**File**: `backend/services/camera_switching.py`

Intelligent camera switching:
- Facecam vs gameplay classification
- Optimal switching point detection
- Timeline generation with transcription sync
- Smooth transition recommendations

### 4. Enhanced Captions
**File**: `backend/services/enhanced_captions.py`

Advanced caption system:
- 8 new caption styles (wave, glow, bounce)
- Smart positioning (avoiding center for gameplay)
- Optimized words-per-line calculation
- Better font scaling for different resolutions

### 5. GPU Optimization
**File**: `backend/services/optimized_processor.py`

Hardware acceleration:
- Auto-detect GPU availability
- FFmpeg GPU arguments generation
- Optimized presets per hardware
- Fallback to CPU when needed

### 6. Batch Processing
**File**: `backend/services/batch_processor.py`

Parallel processing:
- Multi-threaded clip export
- Real-time progress tracking
- Configurable worker count
- Progress callbacks

### 7. Quality Presets
**File**: `backend/services/quality_presets.py`

Platform-optimized presets:
- TikTok (1080x1920, 60fps, 8000k)
- Instagram Reels (1080x1920, 60fps, 8000k)
- YouTube Shorts (1080x1920, 60fps, 8000k)
- YouTube HD (1920x1080, 30fps, 5000k)
- Twitter (1280x720, 30fps, 3000k)
- LinkedIn (1280x720, 30fps, 3000k)
- Facebook (1920x1080, 30fps, 4000k)
- High Quality (1920x1080, 60fps, 10000k)
- Balanced (1280x720, 30fps, 3000k)
- Fast (1280x720, 30fps, 2500k)

### 8. Enhanced UI
**File**: `frontend/src/components/clips-manager.tsx`

Improved clips management:
- Select all/deselect all functionality
- Export options panel (quality, captions, GPU)
- Real-time export progress
- Score breakdown (semantic, heuristic, audio, visual)
- Per-clip preview and export buttons

---

## 📊 API Updates

### New Endpoints

```python
# Enhanced clip finding with multi-modal analysis
POST /api/clips/enhanced-find
{
  "use_audio_analysis": true,
  "use_visual_analysis": true,
  "video_path": "/path/to/video.mp4"
}

# Scene detection
GET /api/clips/scenes/{job_id}
POST /api/clips/detect-scenes

# Camera switching
GET /api/clips/camera-views/{job_id}
POST /api/clips/optimize-switching

# Batch processing
POST /api/clips/batch-export
{
  "clip_ids": ["id1", "id2", "id3"],
  "use_gpu": true,
  "quality_preset": "tiktok",
  "add_captions": true,
  "caption_theme": "viral",
  "caption_style": "karaoke"
}

GET /api/clips/batch-status/{batch_id}

# Quality presets
GET /api/quality/presets
GET /api/quality/recommendations?platform=tiktok
```

---

## 🧪 Performance Improvements

- **2-3x Faster**: GPU-accelerated processing on NVIDIA/Intel hardware
- **Parallel Export**: Multiple clips processed simultaneously
- **Optimized Encoding**: Platform-specific presets for maximum efficiency
- **Smart Caching**: Reuse intermediate files when possible

---

## 🔧 Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
ANTHROPIC_API_KEY=your_anthropic_key

# Optional
HUGGINGFACE_TOKEN=your_huggingface_token
GPU_ENABLED=true
MAX_WORKERS=3
```

### Quality Settings

Quality presets can be customized in `backend/services/quality_presets.py`:

```python
QUALITY_PRESETS = {
    "custom": QualityPreset(
        name="Custom",
        resolution=(width, height),
        fps=fps,
        video_bitrate="bitrate",
        audio_bitrate="audio_bitrate",
        preset="preset",  # fast, medium, slow
        crf=18,  # 0-51, lower is better
    ),
}
```

---

## 📝 Usage Examples

### Upload and Process

```bash
curl -X POST http://localhost:8000/api/upload/url \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://youtube.com/watch?v=...",
    "aspect_ratio": [9, 16],
    "generate_description": true,
    "generate_summary": true
  }'
```

### Find Enhanced Clips

```bash
curl -X POST http://localhost:8000/api/clips/enhanced-find \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "...",
    "use_audio_analysis": true,
    "use_visual_analysis": true
  }'
```

### Batch Export

```bash
curl -X POST http://localhost:8000/api/clips/batch-export \
  -H "Content-Type: application/json" \
  -d '{
    "clip_ids": ["id1", "id2", "id3"],
    "use_gpu": true,
    "quality_preset": "tiktok",
    "add_captions": true,
    "caption_theme": "viral",
    "caption_style": "karaoke"
  }'
```

---

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test

# Integration tests
pytest backend/tests/test_viral_export.py -v
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details

---

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting PRs.

---

**Built with ❤️ by the ClipAI Team.**

*Enhanced with multi-modal analysis, GPU acceleration, and intelligent camera switching.*
