# ClipAI

AI-powered video clipping tool that transforms long videos into viral clips.

![ClipAI](https://img.shields.io/badge/ClipAI-Open%20Source-purple)
![License](https://img.shields.io/badge/License-MIT-green)

## Features

- **AI Clip Detection** - Automatically finds engaging moments using TextTiling algorithm
- **Smart Resizing** - Convert 16:9 to 9:16 with speaker tracking
- **Transcription** - Word-level timestamps with WhisperX
- **AI Descriptions** - Generate viral captions in English & Portuguese
- **Effects & Music** - Add background music, transitions, subtitles
- **Batch Processing** - Process multiple videos in queue

## Tech Stack

- **Frontend**: Next.js 15, React, TailwindCSS, shadcn/ui, Framer Motion
- **Backend**: FastAPI, Python 3.11
- **AI/ML**: ClipsAI, WhisperX, Pyannote, OpenAI/Anthropic
- **Processing**: FFmpeg, MoviePy

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- FFmpeg
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
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install whisperx@git+https://github.com/m-bain/whisperx.git

# Copy environment file
cp .env.example .env
# Edit .env and add your API keys

# Run the server
uvicorn main:app --reload
```

3. **Setup Frontend**
```bash
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

4. **Open the app**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Using Docker

```bash
# Copy environment file
cp backend/.env.example backend/.env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

## Configuration

### Required API Keys

| Key | Purpose | Get From |
|-----|---------|----------|
| `HUGGINGFACE_TOKEN` | Video resizing (Pyannote) | [HuggingFace](https://huggingface.co/settings/tokens) |

### Optional API Keys

| Key | Purpose | Get From |
|-----|---------|----------|
| `OPENAI_API_KEY` | AI descriptions | [OpenAI](https://platform.openai.com/api-keys) |
| `ANTHROPIC_API_KEY` | AI descriptions (alternative) | [Anthropic](https://console.anthropic.com/) |

## API Endpoints

### Upload

```bash
POST /api/upload/
# Upload a video for processing

GET /api/upload/status/{job_id}
# Get processing status

GET /api/upload/job/{job_id}
# Get full job details with clips
```

### Clips

```bash
GET /api/clips/{job_id}
# Get all clips for a job

POST /api/clips/{job_id}/export
# Export selected clips

GET /api/clips/download/{export_id}/{clip_index}
# Download an exported clip
```

## Project Structure

```
clipai/
├── backend/
│   ├── api/
│   │   └── routes/
│   │       ├── upload.py      # Upload endpoints
│   │       └── clips.py       # Clips endpoints
│   ├── services/
│   │   ├── transcriber.py     # WhisperX transcription
│   │   ├── clipper.py         # Clip detection
│   │   ├── resizer.py         # Video resizing
│   │   ├── editor.py          # Video editing
│   │   ├── description.py     # AI descriptions
│   │   └── effects.py         # Effects/music
│   ├── models/
│   │   └── schemas.py         # Pydantic models
│   ├── config.py              # Settings
│   └── main.py                # FastAPI app
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx           # Landing page
│   │   │   └── dashboard/         # Dashboard pages
│   │   └── components/
│   │       └── ui/                # UI components
│   └── package.json
├── docker-compose.yml
└── README.md
```

## How It Works

1. **Upload** - User uploads a video through the web interface
2. **Transcribe** - WhisperX transcribes with word-level timestamps
3. **Find Clips** - TextTiling algorithm detects topic boundaries
4. **Generate Descriptions** - LLM creates viral captions
5. **Export** - Resize, add effects, and download clips

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Credits

- [ClipsAI](https://github.com/ClipsAI/clipsai) - Core clipping library
- [WhisperX](https://github.com/m-bain/whisperX) - Transcription
- [Pyannote](https://github.com/pyannote/pyannote-audio) - Speaker diarization
- [shadcn/ui](https://ui.shadcn.com/) - UI components

---

Built with AI by the ClipAI team.
