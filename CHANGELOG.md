# ClipAI - Changelog

## Version 1.2.0 (Current)

### Major Improvements

#### Backend
- ✅ **Fixed Torch Import Errors** - Added graceful fallback when torch is not available
  - Transcription service now works with CPU-only torch installation
  - Handles ImportError and missing torch modules gracefully
  - Automatic device detection with CPU fallback

- ✅ **All Critical Dependencies Installed**
  - PyTorch (CPU version) installed and working
  - faster-whisper installed and tested
  - sentence-transformers for semantic analysis
  - All ML/AI packages verified: anthropic, openai, google-generativeai
  - Video processing: moviepy, ffmpeg-python, yt-dlp

- ✅ **Enhanced Error Handling**
  - Better error messages throughout backend services
  - Graceful degradation when optional features unavailable
  - Comprehensive logging for debugging

#### Frontend
- ✅ **Real Export Functionality Implemented**
  - Export simulation replaced with actual API calls
  - Real-time progress polling during export
  - Automatic download on completion
  - Support for all export endpoints (single clip, batch export)

- ✅ **Environment Configuration**
  - All hardcoded URLs replaced with `NEXT_PUBLIC_API_URL` environment variable
  - Default fallback to `http://localhost:8000`
  - Easy configuration for production deployments
  - `.env.local` file created for frontend configuration

- ✅ **Updated Components**
  - `clips-manager.tsx` - Full export integration with progress tracking
  - `video-upload.tsx` - Environment-aware API calls
  - `live-transcription.tsx` - Dynamic API URL configuration
  - `clip-card.tsx` - Real export functionality with polling
  - `app/dashboard/clips/page.tsx` - Configured API endpoints
  - `app/dashboard/storage/page.tsx` - Environment-aware storage API

- ✅ **Improved Error Messages**
  - Clear user feedback for connection issues
  - Better error handling for API failures
  - Informative alerts for missing backend

#### Developer Experience
- ✅ **Startup Scripts**
  - `start.bat` - Windows startup script for both frontend and backend
  - `start.sh` - Linux/macOS startup script
  - Automatic process management with proper shutdown handling

- ✅ **Quick Start Guide**
  - `QUICKSTART.md` - Comprehensive installation and troubleshooting guide
  - Step-by-step instructions for all platforms
  - Common issues and solutions
  - Configuration examples

- ✅ **Updated Documentation**
  - README.md enhanced with recent improvements
  - Clear installation steps with fallback options
  - Troubleshooting section for common issues
  - Feature list updated with new capabilities

### Bug Fixes

- Fixed "no module named torch" error - torch now optional with graceful fallback
- Fixed export functionality - now uses real API calls instead of simulation
- Fixed hardcoded API URLs - all configurable via environment variables
- Fixed dependency installation - all packages verified working
- Fixed transcription service - handles CUDA detection failures gracefully

### Technical Details

**Transcription Service Changes:**
```python
# Before: Would crash without torch
import torch
device = "cuda" if torch.cuda.is_available() else "cpu"

# After: Graceful fallback
try:
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
except ImportError:
    device = "cpu"  # Fallback to CPU
```

**Frontend API Configuration:**
```typescript
// Before: Hardcoded URL
fetch("http://localhost:8000/api/upload/")

// After: Configurable
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
fetch(`${API_URL}/api/upload/`)
```

**Export Flow:**
1. User selects clips and clicks export
2. Frontend calls `/api/clips/{jobId}/export/{clipId}`
3. Backend starts background export task
4. Frontend polls `/api/clips/export/{exportId}/status`
5. On completion, automatically downloads the file
6. Real-time progress updates shown to user

### Migration Guide

If upgrading from v1.1.0:

1. **Backend Dependencies:**
   ```bash
   cd backend
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
   pip install faster-whisper sentence-transformers
   ```

2. **Frontend Configuration:**
   ```bash
   cd frontend
   # Create .env.local with API URL
   echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
   ```

3. **Environment Variables:**
   - Edit `backend/.env` to add API keys
   - HUGGINGFACE_TOKEN required for some features
   - GOOGLE_API_KEY recommended for AI features

### Known Limitations

- CPU-only PyTorch (no GPU acceleration)
- Some features require HUGGINGFACE_TOKEN (face tracking, resizing)
- Real-time transcription requires running backend
- Large video processing may take several minutes

### Future Enhancements (Planned)

- [ ] GPU support with CUDA
- [ ] Real-time preview during export
- [ ] Batch export with progress bars
- [ ] Custom caption themes editor
- [ ] Video effects library
- [ ] Social media direct integration

---

## Version 1.1.0 (Previous)

### Initial Features
- Video transcription with faster-whisper
- AI-powered clip detection
- Multi-platform video download (30+ sites)
- Automatic resizing and format conversion
- Basic export functionality
- Dashboard UI with clips management

---

**For detailed feature documentation, see README.md**
