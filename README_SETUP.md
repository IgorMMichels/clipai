# ClipAI Setup Guide

## Prerequisites

- Python 3.10+
- Node.js 18+
- FFmpeg installed (`sudo apt install ffmpeg` or `brew install ffmpeg`)

## Backend Setup

1. Navigate to backend directory:
   ```bash
   cd backend
   ```

2. Create virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
   *Note: If you have issues with `faster-whisper` or `torch`, ensure you have the correct CUDA drivers installed or use the CPU-only versions.*

3. Create `.env` file (optional for API keys):
   ```
   GOOGLE_API_KEY=your_gemini_key
   OPENAI_API_KEY=your_openai_key
   # ...
   ```

4. Run the server:
   ```bash
   python main.py
   ```
   Server will run at `http://localhost:8000`.

## Frontend Setup

1. Navigate to frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run development server:
   ```bash
   npm run dev
   ```
   Frontend will be available at `http://localhost:3000`.

## Features

- **Upload or YouTube:** Paste a link or upload a file.
- **Auto-Transcription:** Uses local AI (Whisper) to transcribe.
- **Viral Clip Detection:** Automatically finds interesting segments.
- **Stacked Layout:** Toggle "Stacked Layout (Facecam)" to auto-crop facecam and gameplay for viral gaming clips.
- **Preview & Export:** Preview clips before rendering high-quality versions.
