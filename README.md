# ClipAI

**AI-powered video clipping and transcription tool.**  
Transform long videos into viral clips, generate intelligent summaries, and transcribe content from 30+ platforms.

![ClipAI](https://img.shields.io/badge/ClipAI-v1.1-purple?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-teal?style=for-the-badge)

## 🚀 Features

### 🎬 Video Clipping (Core)
- **AI Clip Detection** - Automatically finds engaging viral moments using semantic analysis.
- **Smart Resizing** - Converts landscape (16:9) video to portrait (9:16) with active speaker tracking.
- **Facecam Detection** - Intelligent layout handling for gaming/streaming videos.
- **Viral Captions** - Generates social media descriptions and hashtags using AI (Gemini/OpenAI/Anthropic).
- **Video Editor** - Trimming, resizing, and burning subtitles.

### 📝 AI Transcriber (New in v1.1)
- **Multi-Platform Download** - Supports **30+ platforms** including YouTube, TikTok, Instagram, Twitter/X, Bilibili, Vimeo, and more.
- **High-Accuracy Transcription** - Uses **Faster-Whisper** with VAD filtering for precise word-level timestamps.
- **AI Text Optimization** - Automatically fixes typos, punctuation, and grammar using LLMs.
- **Intelligent Summarization** - Generates comprehensive summaries, key points, and topic lists in **20+ languages**.
- **Translation Service** - Translates transcripts between languages with auto-detection.
- **Real-Time Progress** - Live progress tracking via Server-Sent Events (SSE).
- **Export Formats** - Download results in Markdown, SRT, VTT, and JSON.

---

## 🛠️ Tech Stack

- **Backend**: FastAPI, Python 3.11+
- **Frontend**: Next.js 15, React, TailwindCSS, shadcn/ui
- **AI/ML**: 
  - **Transcription**: Faster-Whisper
  - **LLMs**: Google Gemini 2.0, OpenAI GPT-4o, Anthropic Claude
  - **Embeddings**: Sentence-Transformers
  - **Vision**: OpenCV, MediaPipe (Face detection)
- **Processing**: FFmpeg, MoviePy, yt-dlp

---

## ⚡ Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- FFmpeg (must be installed on your system)
- libmagic

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/clipai.git
   cd clipai
   ```

2. **Setup Backend**
   ```bash
   cd backend
   
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Setup environment variables
   cp .env.example .env
   # Edit .env with your API keys (OPENAI_API_KEY, GOOGLE_API_KEY, etc.)
   
   # Run the server
   uvicorn main:app --reload
   ```

3. **Setup Frontend**
   ```bash
   cd frontend
   
   # Install dependencies
   npm install
   
   # Run development server
   npm run dev
   ```

4. **Access the Application**
   - Frontend: `http://localhost:3000`
   - Backend API: `http://localhost:8000`
   - API Docs: `http://localhost:8000/docs`

### 🐳 Using Docker

```bash
# Copy env file
cp backend/.env.example backend/.env

# Start services
docker-compose up -d

# View logs
docker-compose logs -f
```

---

## 📖 API Documentation

### 1. Transcription & Summary API (Standalone)

**Transcribe from URL (30+ platforms supported):**
```http
POST /api/transcribe/url
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=...",
  "language": "en",           // Optional: Source language (auto-detect if null)
  "generate_summary": true,   // Generate AI summary
  "summary_language": "es",   // Optional: Output summary in Spanish
  "generate_translation": true,
  "translation_language": "es"
}
```

**Transcribe from File:**
```http
POST /api/transcribe/file
Content-Type: multipart/form-data

file: (binary video/audio file)
generate_summary: true
```

**Stream Progress (SSE):**
```http
GET /api/transcribe/stream/{job_id}
```

**Get Results:**
```http
GET /api/transcribe/result/{job_id}
```

**Export:**
```http
GET /api/transcribe/export/{job_id}  // Download Markdown
```

### 2. Video Clipping API

**Upload & Process:**
```http
POST /api/upload/url
Content-Type: application/json

{
  "url": "https://www.tiktok.com/@user/video/...",
  "aspect_ratio": [9, 16],
  "generate_description": true,
  "generate_summary": true
}
```

**Get Detected Clips:**
```http
GET /api/clips/{job_id}
```

---

## 🌍 Supported Platforms & Languages

### Video Platforms
Supports downloading from **30+ sites** including:
- YouTube, TikTok, Instagram, Facebook, Twitter/X
- Bilibili, Vimeo, Twitch, Reddit, LinkedIn
- Pinterest, Tumblr, SoundCloud, and many more.

### Summary Languages
English, Chinese (Simplified/Traditional), Japanese, Korean, Spanish, French, German, Portuguese, Russian, Arabic, Hindi, Italian, Dutch, Polish, Turkish, Vietnamese, Thai, Indonesian, Malay, Ukrainian.

---

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

**Built with ❤️ by the ClipAI Team.**
