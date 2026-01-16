# ClipAI - Troubleshooting Guide

## Backend Issues

### "ModuleNotFoundError: No module named 'torch'"

**Cause**: PyTorch not installed or incompatible version

**Solutions**:

1. **Install PyTorch (CPU version - Recommended for Windows)**
   ```bash
   cd backend
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
   ```

2. **Install PyTorch (GPU version - requires CUDA)**
   ```bash
   cd backend
   # Check your CUDA version first
   nvidia-smi
   # Then install matching version from https://pytorch.org/get-started/locally/
   ```

3. **Verify Installation**
   ```bash
   python -c "import torch; print(torch.__version__)"
   ```

### "ModuleNotFoundError: No module named 'faster_whisper'"

**Cause**: faster-whisper package not installed

**Solution**:
```bash
cd backend
pip install faster-whisper
```

### "ModuleNotFoundError: No module named 'sentence_transformers'"

**Cause**: sentence-transformers package not installed

**Solution**:
```bash
cd backend
pip install sentence-transformers
```

### Backend fails to start with import errors

**Cause**: Missing dependencies

**Solution**:
```bash
cd backend
pip install -r requirements.txt
```

If requirements.txt fails due to numpy compilation:
```bash
pip install numpy
pip install -r requirements.txt
```

### Port 8000 already in use

**Cause**: Another process is using port 8000

**Solutions**:

**Windows**:
```cmd
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Linux/macOS**:
```bash
lsof -ti:8000 | xargs kill -9
```

Or change port in `backend/main.py`:
```python
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,  # Change to 8001
        reload=settings.DEBUG,
    )
```

## Frontend Issues

### Frontend can't connect to backend

**Cause**: Backend not running or wrong API URL

**Solutions**:

1. **Check if backend is running**
   - Visit http://localhost:8000/api/health
   - Should see: `{"status": "healthy"}`

2. **Check API URL configuration**
   ```bash
   # frontend/.env.local
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. **Clear Next.js cache and restart**
   ```bash
   cd frontend
   rm -rf .next
   npm run dev
   ```

### "NEXT_PUBLIC_API_URL is not defined"

**Cause**: Environment file not created

**Solution**:
```bash
cd frontend
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
# Restart the dev server
```

### Export button does nothing

**Cause**: Backend export endpoint not working

**Solutions**:

1. **Check browser console for errors** (F12)
2. **Verify backend export endpoint**
   ```bash
   curl http://localhost:8000/api/clips
   ```
3. **Check backend logs for export errors**

### Export progress stuck

**Cause**: Background task failed or stuck

**Solutions**:

1. **Check backend logs** - look for export errors
2. **Try exporting smaller clips** (30-60 seconds)
3. **Restart backend** to clear stuck tasks

## Video Processing Issues

### FFmpeg not found

**Cause**: FFmpeg not installed or not in PATH

**Solutions**:

**Windows**:
1. Download from https://ffmpeg.org/download.html
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to System PATH
4. Restart terminal/command prompt
5. Verify: `ffmpeg -version`

**macOS** (Homebrew):
```bash
brew install ffmpeg
```

**Linux** (Ubuntu/Debian):
```bash
sudo apt-get install ffmpeg
```

### "Video file not found" error

**Cause**: File was deleted or path incorrect

**Solution**:
- Check Storage Manager for uploaded files
- Re-upload the video if missing
- Check `backend/uploads/` directory

### Transcription fails with timeout

**Cause**: Video too long or system resources low

**Solutions**:

1. **Use smaller video files** (< 30 minutes recommended)
2. **Close other applications** to free up resources
3. **Check system memory** - at least 8GB recommended

## API Key Issues

### "HUGGINGFACE_TOKEN not set"

**Cause**: Missing environment variable for Pyannote (face tracking)

**Solution**:

1. **Get token from HuggingFace**
   - Visit https://huggingface.co/settings/tokens
   - Create new token (read permissions)

2. **Add to .env file**
   ```bash
   cd backend
   # Edit .env
   HUGGINGFACE_TOKEN=hf_your_token_here
   ```

3. **Restart backend**

### AI features not working (description, captions)

**Cause**: Missing or invalid API keys

**Solution**:

**Google Gemini (Recommended - Free tier)**:
1. Visit https://aistudio.google.com/app/apikey
2. Create API key
3. Add to `backend/.env`:
   ```
   GOOGLE_API_KEY=your_gemini_api_key
   ```
4. Restart backend

**OpenAI (Alternative)**:
1. Visit https://platform.openai.com/api-keys
2. Create API key
3. Add to `backend/.env`:
   ```
   OPENAI_API_KEY=your_openai_api_key
   ```

**Anthropic (Alternative)**:
1. Visit https://console.anthropic.com/
2. Create API key
3. Add to `backend/.env`:
   ```
   ANTHROPIC_API_KEY=your_anthropic_api_key
   ```

## Performance Issues

### Slow video processing

**Cause**: CPU-only processing or large files

**Solutions**:

1. **Use smaller clips** (1-3 minutes ideal for clips)
2. **Enable GPU acceleration** (if you have NVIDIA GPU)
   - Install CUDA-enabled PyTorch
   - Set `CUDA_VISIBLE_DEVICES=0` environment variable
3. **Close other applications**
4. **Use smaller Whisper model**
   - Edit `backend/services/transcriber.py`
   - Change `model_size = "small"` to `"tiny"` or `"base"`

### Out of memory errors

**Cause**: Video file too large for available RAM

**Solutions**:

1. **Process smaller video segments**
2. **Increase system RAM** or use system with more memory
3. **Close other applications**
4. **Reduce video quality** before uploading

## Development Issues

### Next.js build errors

**Cause**: TypeScript errors or missing dependencies

**Solutions**:

```bash
cd frontend
rm -rf .next node_modules
npm install
npm run dev
```

### Python import errors in backend

**Cause**: Virtual environment issues

**Solutions**:

```bash
cd backend

# Create new virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/macOS)
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Changes not reflecting

**Cause**: Browser caching or build cache

**Solutions**:

1. **Hard refresh**: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
2. **Clear Next.js cache**:
   ```bash
   cd frontend
   rm -rf .next
   npm run dev
   ```
3. **Clear browser cache and cookies**

## Getting Help

If none of the solutions work:

1. **Check logs**
   - Backend: Look at terminal where backend is running
   - Frontend: Check browser console (F12)

2. **Verify requirements**
   - Python 3.11+ (`python --version`)
   - Node.js 20+ (`node --version`)
   - FFmpeg installed (`ffmpeg -version`)

3. **Test API endpoints**
   - Visit http://localhost:8000/docs
   - Try API calls from the docs

4. **Check issues**
   - Look at GitHub issues for similar problems
   - Search error messages in issues

5. **Provide detailed info when asking for help**:
   - OS and version
   - Python and Node.js versions
   - Error messages (full stack trace)
   - Steps to reproduce
   - What you've tried so far
