# How to Run ClipAI

## Prerequisites Check

Before starting, verify you have:

```bash
# Check Python (3.11+)
python --version

# Check Node.js (20+)
node --version

# Check FFmpeg
ffmpeg -version

# All should work without errors
```

---

## Option 1: Startup Scripts (Recommended)

### Windows
```bash
# Double-click this file in File Explorer
start.bat
```

### Linux/macOS
```bash
# Make executable (first time only)
chmod +x start.sh

# Run
./start.sh
```

**What the scripts do:**
1. Start backend server on port 8000
2. Start frontend server on port 3000
3. Wait 3 seconds for backend to initialize
4. Display URLs and status

---

## Option 2: Manual Startup

### Step 1: Start Backend

**Open Terminal 1:**
```bash
cd backend

# (Optional) Create virtual environment
python -m venv venv
# Activate venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/macOS

# Install dependencies (first time only)
pip install -r requirements.txt

# Create .env file (first time only)
cp .env.example .env
# Edit .env with your API keys:
# GOOGLE_API_KEY=your_key
# HUGGINGFACE_TOKEN=your_token

# Start server
python main.py
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**Wait until you see:** `INFO:     Application startup complete.`

---

### Step 2: Start Frontend

**Open Terminal 2:**
```bash
cd frontend

# Install dependencies (first time only)
npm install

# Create .env.local (first time only)
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start dev server
npm run dev
```

**Expected output:**
```
ready - started server on 0.0.0.0:3000, url: http://localhost:3000
```

---

## Accessing the Application

Once both servers are running:

### Frontend
- **URL**: http://localhost:3000
- Open in your web browser

### Backend API
- **URL**: http://localhost:8000
- **Health Check**: http://localhost:8000/api/health
- **API Docs**: http://localhost:8000/docs

---

## Testing the Application

### 1. Upload a Video
1. Go to http://localhost:3000/dashboard/upload
2. Drag & drop a video file OR
3. Paste a YouTube URL and click "Process"
4. Watch real-time progress

### 2. View Detected Clips
1. After processing completes, you'll see detected clips
2. Each clip shows:
   - AI virality score
   - Transcript text
   - Duration
3. Click "Preview" to see a preview

### 3. Export Clips
1. Select clips you want to export
2. Configure export settings:
   - Quality preset (TikTok, Instagram, etc.)
   - Caption theme (Viral, Gradient, etc.)
   - GPU acceleration, scene detection, etc.
3. Click "Export Selected"
4. Watch real-time progress
5. File automatically downloads when complete

---

## Common Startup Issues

### Issue: "ModuleNotFoundError: No module named 'torch'"

**Solution:**
```bash
cd backend
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### Issue: "ModuleNotFoundError: No module named 'faster_whisper'"

**Solution:**
```bash
cd backend
pip install faster-whisper
```

### Issue: Port 8000 already in use

**Solution:**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/macOS
lsof -ti:8000 | xargs kill -9
```

### Issue: Port 3000 already in use

**Solution:**
```bash
# Kill Next.js process and restart
# Windows: Ctrl+C in frontend terminal
# Then: npm run dev

# Or kill process manually:
# Windows
taskkill /F /IM node.exe
# Linux/macOS
killall node
```

### Issue: Frontend can't connect to backend

**Solution:**
```bash
# 1. Check if backend is running
curl http://localhost:8000/api/health

# 2. Check frontend configuration
cd frontend
cat .env.local
# Should see: NEXT_PUBLIC_API_URL=http://localhost:8000

# 3. If .env.local doesn't exist, create it:
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
# Restart frontend
```

---

## Development Workflow

### Watching for Changes

**Backend**:
- `python main.py` has auto-reload enabled
- Save Python files → backend restarts automatically

**Frontend**:
- `npm run dev` has hot reload enabled
- Save TypeScript/React files → page updates automatically

### Debugging

**Backend Logs:**
- View in terminal where backend is running
- Errors show in red, info in blue

**Frontend Logs:**
- Open browser console (F12)
- Click "Console" tab
- Errors and warnings appear here

### Testing API Endpoints

Visit http://localhost:8000/docs to:
- View all available endpoints
- Try API calls directly
- See request/response formats

---

## Stopping the Application

### Using Startup Scripts

Press `Ctrl+C` in the terminal running the scripts
Both servers will stop gracefully

### Manual Stop

**Backend:**
Press `Ctrl+C` in the backend terminal

**Frontend:**
Press `Ctrl+C` in the frontend terminal

---

## Next Steps

1. **Add API Keys** (for AI features)
   - Edit `backend/.env`
   - Add `GOOGLE_API_KEY` (recommended)
   - Add `HUGGINGFACE_TOKEN` (for face tracking)
   - Restart backend

2. **Explore Features**
   - Upload test videos
   - Try different export settings
   - Explore all dashboard pages

3. **Customize**
   - Modify themes in `frontend/src/app/globals.css`
   - Adjust processing settings in backend services
   - Add custom caption styles

---

## Getting Help

If you encounter issues:

1. Check the terminal output for errors
2. Visit [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
3. Check API documentation at http://localhost:8000/docs
4. Review [SUMMARY_OF_CHANGES.md](SUMMARY_OF_CHANGES.md) for recent fixes

---

**Quick Reference:**

| What | Command |
|-------|----------|
| Start (auto) | `start.bat` or `./start.sh` |
| Start backend | `cd backend && python main.py` |
| Start frontend | `cd frontend && npm run dev` |
| Check health | `curl http://localhost:8000/api/health` |
| API docs | Visit http://localhost:8000/docs |

**Happy Clipping! 🎬✨**
