#!/usr/bin/env python
"""Startup check script for ClipAI backend"""

import sys

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'faster_whisper',
        'torch',
        'google.generativeai',
        'openai',
        'anthropic',
        'moviepy',
        'sentence_transformers',
        'yt_dlp',
        'ffmpeg_python',
    ]
    
    missing = []
    for pkg in required_packages:
        try:
            __import__(pkg.replace('-', '_'))
            print(f"✓ {pkg}")
        except ImportError as e:
            print(f"✗ {pkg}: {e}")
            missing.append(pkg)
    
    if missing:
        print(f"\n❌ Missing packages: {missing}")
        return False
    
    print("\n✓ All dependencies are installed!")
    return True

def check_directories():
    """Check if required directories exist"""
    from pathlib import Path
    import os
    from dotenv import load_dotenv
    
    load_dotenv('.env')
    load_dotenv('.env.local')
    
    # Get paths from environment or defaults
    base_dir = Path(__file__).parent
    upload_dir = base_dir.parent / "uploads"
    output_dir = base_dir.parent / "outputs"
    
    # Create directories
    upload_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n✓ Upload directory: {upload_dir}")
    print(f"✓ Output directory: {output_dir}")

def check_ffmpeg():
    """Check if FFmpeg is installed"""
    import subprocess
    
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                           capture_output=True, 
                           text=True,
                           timeout=2)
        if result.returncode == 0:
            print("\n✓ FFmpeg is installed")
            return True
    except:
        pass
    
    print("\n⚠️  FFmpeg not found in PATH")
    print("   Install from: https://ffmpeg.org/download.html")
    return False

def check_config():
    """Check configuration"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv('.env')
    load_dotenv('.env.local')
    
    print("\nConfiguration:")
    api_keys = {
        'GOOGLE_API_KEY': '✓' if os.getenv('GOOGLE_API_KEY') else '⚠️  Not set (optional)',
        'OPENAI_API_KEY': '✓' if os.getenv('OPENAI_API_KEY') else '⚠️  Not set (optional)',
        'ANTHROPIC_API_KEY': '✓' if os.getenv('ANTHROPIC_API_KEY') else '⚠️  Not set (optional)',
        'HUGGINGFACE_TOKEN': '✓' if os.getenv('HUGGINGFACE_TOKEN') else '⚠️  Not set (optional)',
    }
    
    for key, status in api_keys.items():
        print(f"  {key}: {status}")

def main():
    print("=" * 50)
    print("ClipAI Backend Startup Check")
    print("=" * 50)
    
    all_good = True
    
    if not check_dependencies():
        all_good = False
    
    check_directories()
    check_config()
    check_ffmpeg()
    
    print("\n" + "=" * 50)
    if all_good:
        print("✓ All checks passed! Ready to start.")
        print("  Run: python main.py")
    else:
        print("❌ Some checks failed. Please fix issues above.")
        sys.exit(1)
    print("=" * 50)

if __name__ == "__main__":
    main()
