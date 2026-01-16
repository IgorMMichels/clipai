# ClipAI - Quick Start Guide

## Prerequisites

Before running ClipAI, ensure you have:

1. **Python 3.11+** - [Download here](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"
   - Verify with: `python --version`

2. **Node.js 20+** - [Download here](https://nodejs.org/)
   - Verify with: `node --version`

3. **FFmpeg** - [Download here](https://ffmpeg.org/download.html)
   - Add FFmpeg to your system PATH
   - Verify with: `ffmpeg -version`

## Installation

### 1. Clone the Repository (if not already done)

```bash
git clone <your-repo-url>
cd clipai
```

### 2. Backend Setup

```bash
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# (Optional) Edit .env and add your API keys:
# - GOOGLE_API_KEY (recommended - free tier available)
# - HUGGINGFACE_TOKEN (required for some features)
# - OPENAI_API_KEY (alternative to Google)
```

### 3. Frontend Setup

```bash
cd ../frontend

# Install Node.js dependencies
npm install
```

## Running ClipAI

### Option 1: Using Startup Scripts (Recommended)

**Windows:**
```bash
# Double-click start.bat
# Or run from command line:
start.bat
```

**Linux/macOS:**
```bash
chmod +x start.sh
./start.sh
```

### Option 2: Manual Startup

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

## Accessing ClipAI

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Common Issues & Solutions

### Issue: "No module named torch"
- **Solution**: Run `cd backend && pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu`

### Issue: "No module named faster_whisper"
- **Solution**: Run `cd backend && pip install faster-whisper`

### Issue: Backend fails to start
- **Solution**: 
  1. Check if port 8000 is already in use
  2. Run `cd backend && python -c "from main import app; print('OK')"` to test imports
  3. Check backend logs for error messages

### Issue: Frontend fails to connect to backend
- **Solution**:
  1. Ensure backend is running at http://localhost:8000
  2. Check that `NEXT_PUBLIC_API_URL` in frontend/.env.local is set to `http://localhost:8000`
  3. Try accessing http://localhost:8000/api/health in your browser

### Issue: FFmpeg not found
- **Solution**: 
  1. Install FFmpeg from https://ffmpeg.org/download.html
  2. Add FFmpeg installation directory to your system PATH
  3. Restart your terminal/command prompt

## Configuration

### Environment Variables (Backend)

Edit `backend/.env`:

```bash
# Required for video resizing (Pyannote)
HUGGINGFACE_TOKEN=your_token_here

# Recommended - Free tier available!
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional - Alternative LLM providers
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Debug mode
DEBUG=true
```

### Environment Variables (Frontend)

Edit `frontend/.env.local` (create if it doesn't exist):

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Features

### Video Upload
- **File Upload**: Drag & drop or browse for video files (MP4, MOV, AVI, MKV, WebM, max 500MB)
- **YouTube Download**: Paste YouTube URLs to download and process directly

### AI-Powered Processing
- **Automatic Transcription**: Word-level timestamps with AI text optimization
- **Clip Detection**: AI scores clips to find viral-worthy moments
- **Smart Resizing**: Converts landscape videos to portrait (9:16) with speaker tracking

### Export Options
- **Quality Presets**: TikTok, Instagram Reels, YouTube Shorts, and more
- **Caption Styles**: Viral, Gradient, Bounce, Glow, and Karaoke
- **Real-time Progress**: Live updates during processing and export

## API Documentation

Once the backend is running, visit http://localhost:8000/docs to see interactive API documentation.

## Support

For issues or questions:
1. Check the logs in the terminal where the servers are running
2. Visit the API documentation at http://localhost:8000/docs
3. Check the main README.md for detailed information

---

**Built with ❤️ by the ClipAI Team**
