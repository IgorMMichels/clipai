# ClipAI - Deployment Guide

## Overview

ClipAI is a full-stack application with:
- **Backend**: FastAPI (Python) on port 8000
- **Frontend**: Next.js (React) on port 3000

## Quick Deployment

### Option 1: Local Development

**Prerequisites:**
- Python 3.11+
- Node.js 20+
- FFmpeg installed and in PATH

**Steps:**
```bash
# 1. Clone and navigate
cd clipai

# 2. Backend setup
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys

# 3. Frontend setup
cd ../frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# 4. Start servers (in separate terminals)
# Terminal 1:
cd backend
python main.py

# Terminal 2:
cd frontend
npm run dev

# Or use startup scripts:
# Windows: start.bat
# Linux/macOS: ./start.sh
```

### Option 2: Docker Deployment

**Prerequisites:**
- Docker
- Docker Compose

**Steps:**
```bash
# 1. Setup environment
cd backend
cp .env.example .env
# Edit .env with your API keys
cd ..

# 2. Build and start
docker-compose up -d

# 3. View logs
docker-compose logs -f

# 4. Stop
docker-compose down
```

### Option 3: Production Deployment

#### Backend Deployment (PythonAnywhere, Railway, Render, etc.)

**1. Prepare Backend**
```bash
cd backend
# Update config.py for production:
DEBUG = False
BASE_DIR = Path(__file__).resolve().parent
# Set CORS origins to your frontend domain
```

**2. Install Dependencies**
```bash
pip install -r requirements.txt
pip install gunicorn
```

**3. Configure Environment Variables**
Set these in your hosting platform:
- `GOOGLE_API_KEY` - For AI features
- `HUGGINGFACE_TOKEN` - For face tracking
- `OPENAI_API_KEY` - Alternative LLM (optional)
- `ANTHROPIC_API_KEY` - Alternative LLM (optional)
- `DEBUG` - Set to `false`

**4. Start with Gunicorn**
```bash
gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
```

#### Frontend Deployment (Vercel, Netlify, etc.)

**1. Configure Environment Variable**
In your hosting platform, set:
```
NEXT_PUBLIC_API_URL=https://your-backend-domain.com
```

**2. Build and Deploy**
```bash
cd frontend
npm run build
# Upload .next directory or use platform's CLI
```

**For Vercel:**
```bash
npm i -g vercel
vercel
# Set NEXT_PUBLIC_API_URL in project settings
```

**For Netlify:**
```bash
# Add netlify.toml:
[build]
  command = "npm run build"
  publish = ".next"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

## Environment Variables

### Backend (.env)

```bash
# Required for face tracking (Pyannote)
HUGGINGFACE_TOKEN=hf_your_token_here

# Recommended for AI features
GOOGLE_API_KEY=your_gemini_key_here

# Optional: Alternative LLM providers
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Debug mode
DEBUG=false  # Always false in production

# Optional: Redis for task queue
REDIS_URL=redis://localhost:6379/0
```

### Frontend (.env.local)

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
# Production: https://api.yourdomain.com
```

## Performance Optimization

### Backend

1. **Use GPU for ML processing** (if available)
   - Install CUDA-enabled PyTorch
   - Set `CUDA_VISIBLE_DEVICES=0`
   - Whisper will automatically use GPU

2. **Enable Caching**
   ```python
   # In main.py
   from fastapi_cache import FastAPICache
   cache = FastAPICache()
   ```

3. **Use Worker Processes**
   ```bash
   gunicorn main:app --workers 4
   ```

4. **Configure File Cleanup**
   - Backend auto-cleans files older than 7 days
   - Adjust in `backend/api/routes/clips.py`

### Frontend

1. **Enable Next.js Production Build**
   ```bash
   npm run build
   npm start  # Instead of npm run dev
   ```

2. **Configure CDN for Assets**
   - Upload `public/` to CDN
   - Update asset URLs

3. **Enable Caching**
   ```javascript
   // In next.config.ts
   module.exports = {
     async headers() {
       return [
         {
           source: '/:path*',
           headers: [
             { key: 'Cache-Control', value: 'public, max-age=31536000' },
           ],
         },
       ]
     },
   }
   ```

## Security Considerations

### Backend

1. **Enable HTTPS**
   ```python
   # main.py
   if __name__ == "__main__":
       uvicorn.run(
           "main:app",
           host="0.0.0.0",
           port=8000,
           ssl_keyfile="path/to/key.pem",
           ssl_certfile="path/to/cert.pem"
       )
   ```

2. **Set CORS Origins**
   ```python
   # main.py
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://yourdomain.com"],  # Restrict to your domain
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

3. **Use Environment Variables for Secrets**
   - Never commit API keys to git
   - Use `.env` files (in .gitignore)
   - Use platform's secret management in production

4. **Add Rate Limiting**
   ```python
   from fastapi.middleware import Middleware
   from slowapi import Limiter, _rate_limit_exceeded_handler
   
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   
   @app.get("/api/...")
   @limiter.limit("10/minute")
   async def endpoint():
       pass
   ```

### Frontend

1. **Secure Environment Variables**
   - Never expose API keys in client-side code
   - Only use `NEXT_PUBLIC_` prefixed variables

2. **Enable Content Security Policy**
   ```javascript
   // next.config.ts
   module.exports = {
     async headers() {
       return [
         {
           source: '/:path*',
           headers: [
             {
               key: 'Content-Security-Policy',
               value: "default-src 'self'; script-src 'self' 'unsafe-inline'"
             },
           ],
         },
       ]
     },
   }
   ```

## Monitoring

### Backend Logs

```bash
# View live logs
tail -f backend.log

# Search for errors
grep "ERROR" backend.log

# Export logs
cp backend.log backup_$(date +%Y%m%d).log
```

### Frontend Logs

- Browser console (F12)
- Next.js build logs during deployment
- Server logs for server errors

### Health Checks

```bash
# Backend health
curl http://localhost:8000/api/health
# Expected: {"status": "healthy"}

# Frontend availability
curl http://localhost:3000
# Expected: HTML response
```

## Backup and Recovery

### Database Backup

ClipAI uses in-memory storage by default. To enable persistence:

```python
# In config.py
DATABASE_URL = "sqlite+aiosqlite:///./data/clipai.db"
```

### File Backup

```bash
# Backup uploads
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz uploads/

# Backup outputs
tar -czf outputs_backup_$(date +%Y%m%d).tar.gz outputs/

# Backup environment files
cp .env .env.backup_$(date +%Y%m%d)
```

### Restore

```bash
# Restore files
tar -xzf uploads_backup_YYYYMMDD.tar.gz
tar -xzf outputs_backup_YYYYMMDD.tar.gz

# Restore environment
cp .env.backup_YYYYMMDD .env
```

## Scaling

### Horizontal Scaling

**Backend:**
- Use load balancer (nginx, HAProxy)
- Run multiple instances on different ports
- Share database/storage via network

**Frontend:**
- Static site can be served by CDN
- API calls go through backend load balancer

### Vertical Scaling

**Backend:**
- More CPU cores → faster transcription
- More RAM → process larger videos
- GPU → 10x faster ML processing

**Frontend:**
- Next.js scales automatically
- CDN serves static assets

## Troubleshooting

### Port Conflicts

```bash
# Find what's using port 8000
netstat -ano | findstr :8000  # Windows
lsof -ti:8000  # Linux/macOS

# Change port in main.py
uvicorn.run("main:app", port=8001)
```

### Memory Issues

```bash
# Monitor memory
htop  # Linux/macOS
taskmgr  # Windows

# Increase swap space (Linux)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Slow Performance

1. Check CPU usage: `top` or `htop`
2. Check disk I/O: `iostat`
3.
