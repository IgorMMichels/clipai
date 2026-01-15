"""
Optimized Video Processing Service with GPU Acceleration
Fast video processing with optional GPU support
"""
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import platform
import re

logger = logging.getLogger(__name__)


class OptimizedVideoProcessor:
    """Optimized video processing with GPU acceleration"""

    def __init__(self):
        self._gpu_available = self._check_gpu_availability()
        self._gpu_device = self._detect_gpu_device()

        if self._gpu_available:
            logger.info(f"GPU acceleration available: {self._gpu_device}")
        else:
            logger.info("GPU acceleration not available, using CPU processing")

    def _check_gpu_availability(self) -> bool:
        """Check if GPU acceleration is available"""
        try:
            # Check for NVIDIA GPU
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    return True

            # Check for FFmpeg GPU support
            result = subprocess.run(
                ["ffmpeg", "-hwaccels"],
                capture_output=True,
                timeout=5
            )
            if "cuda" in result.stdout.lower() or "nvenc" in result.stdout.lower():
                return True

            return False

        except Exception as e:
            logger.debug(f"GPU check failed: {e}")
            return False

    def _detect_gpu_device(self) -> str:
        """Detect the GPU device for FFmpeg"""
        try:
            result = subprocess.run(
                ["ffmpeg", "-hwaccels"],
                capture_output=True,
                timeout=5
            )
            hwaccels = result.stdout.lower()

            if "cuda" in hwaccels:
                return "cuda"
            elif "nvenc" in hwaccels:
                return "nvenc"
            elif "qsv" in hwaccels:
                return "qsv"  # Intel Quick Sync
            elif "videotoolbox" in hwaccels:
                return "videotoolbox"  # macOS
            else:
                return "none"

        except Exception as e:
            logger.debug(f"GPU detection failed: {e}")
            return "none"

    def get_ffmpeg_gpu_args(self) -> List[str]:
        """Get FFmpeg arguments for GPU acceleration"""
        if self._gpu_device == "cuda":
            return [
                "-hwaccel", "cuda",
                "-hwaccel_output_format", "cuda",
            ]
        elif self._gpu_device == "nvenc":
            return [
                "-hwaccel", "cuda",
                "-c:v", "h264_nvenc",
            ]
        elif self._gpu_device == "qsv":
            return [
                "-hwaccel", "qsv",
                "-c:v", "h264_qsv",
            ]
        elif self._gpu_device == "videotoolbox":
            return [
                "-hwaccel", "videotoolbox",
                "-c:v", "h264_videotoolbox",
            ]
        else:
            return []

    def get_optimized_preset(self, speed: str = "medium") -> str:
        """Get optimized preset based on speed and GPU availability"""
        if self._gpu_available:
            # GPU can handle faster encoding
            speed_map = {
                "fast": "p1",
                "medium": "p4",
                "slow": "p6",
            }
            return speed_map.get(speed, "p4")
        else:
            # CPU presets
            return speed

    def fast_trim(
        self,
        input_path: Path,
        output_path: Path,
        start_time: float,
        end_time: float,
        use_gpu: bool = True,
        speed: str = "fast",
    ) -> Path:
        """
        Fast video trimming with optional GPU acceleration

        Args:
            input_path: Input video path
            output_path: Output video path
            start_time: Start time in seconds
            end_time: End time in seconds
            use_gpu: Use GPU acceleration if available
            speed: Encoding speed (fast, medium, slow)

        Returns:
            Path to trimmed video
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        duration = end_time - start_time

        # Build command with optional GPU
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_time),
            "-i", str(input_path),
            "-t", str(duration),
        ]

        # Add GPU acceleration if available
        if use_gpu and self._gpu_available:
            cmd.extend(self.get_ffmpeg_gpu_args())
        else:
            cmd.extend(["-c:v", "libx264"])

        # Add preset
        cmd.extend([
            "-preset", self.get_optimized_preset(speed),
            "-crf", "18",  # High quality
            "-c:a", "aac",
            "-b:a", "192k",
            str(output_path)
        ])

        logger.info(f"Fast trimming video (GPU: {use_gpu and self._gpu_available})")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            raise RuntimeError(f"Failed to trim video: {result.stderr}")

        logger.info(f"Trimmed video saved: {output_path}")
        return output_path

    def fast_resize(
        self,
        input_path: Path,
        output_path: Path,
        width: int,
        height: int,
        use_gpu: bool = True,
        speed: str = "fast",
    ) -> Path:
        """
        Fast video resizing with GPU acceleration

        Args:
            input_path: Input video path
            output_path: Output video path
            width: Target width
            height: Target height
            use_gpu: Use GPU acceleration if available
            speed: Encoding speed

        Returns:
            Path to resized video
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Build scale filter
        scale_filter = f"scale={width}:{height}"

        # Build command
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
        ]

        # Add GPU acceleration
        if use_gpu and self._gpu_available:
            gpu_args = self.get_ffmpeg_gpu_args()
            if "-c:v" not in gpu_args:
                cmd.extend(gpu_args)

        cmd.extend([
            "-vf", scale_filter,
        ])

        if use_gpu and self._gpu_available:
            if "-c:v" not in self.get_ffmpeg_gpu_args():
                cmd.extend(["-c:v", "libx264"])

        cmd.extend([
            "-preset", self.get_optimized_preset(speed),
            "-crf", "20",
            "-c:a", "aac",
            "-b:a", "128k",
            str(output_path)
        ])

        logger.info(f"Fast resizing video (GPU: {use_gpu and self._gpu_available})")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            raise RuntimeError(f"Failed to resize video: {result.stderr}")

        logger.info(f"Resized video saved: {output_path}")
        return output_path

    def fast_composite(
        self,
        input_path: Path,
        output_path: Path,
        facecam_path: Optional[Path] = None,
        pip_position: str = "bottom-right",
        pip_scale: float = 0.3,
        use_gpu: bool = True,
        speed: str = "medium",
    ) -> Path:
        """
        Fast video compositing with PiP using GPU acceleration

        Args:
            input_path: Main video path
            output_path: Output video path
            facecam_path: Optional facecam video path for PiP
            pip_position: PiP position (bottom-right, etc.)
            pip_scale: PiP size relative to main video
            use_gpu: Use GPU acceleration if available
            speed: Encoding speed

        Returns:
            Path to composited video
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Get main video dimensions
        width, height = 1080, 1920

        # Build filter chain
        filter_parts = []

        if facecam_path and facecam_path.exists():
            # Calculate PiP dimensions
            pip_width = int(width * pip_scale)
            pip_height = int(pip_width * 0.75)  # 4:3 aspect ratio

            # Calculate PiP position
            margin = 40
            if pip_position == "top-left":
                x, y = margin, margin
            elif pip_position == "top-right":
                x, y = width - pip_width - margin, margin
            elif pip_position == "bottom-left":
                x, y = margin, height - pip_height - margin
            else:  # bottom-right
                x, y = width - pip_width - margin, height - pip_height - margin

            # Create PiP filter
            pip_filter = (
                f"[1:v]scale={pip_width}:{pip_height}[pip];"
                f"[0:v][pip]overlay={x}:{y}"
            )
            filter_parts.append(pip_filter)
        else:
            # Just resize
            filter_parts.append(f"scale={width}:{height}")

        filter_complex = ";".join(filter_parts)

        # Build command
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
        ]

        if facecam_path and facecam_path.exists():
            cmd.extend(["-i", str(facecam_path)])

        # Add GPU acceleration
        if use_gpu and self._gpu_available:
            gpu_args = self.get_ffmpeg_gpu_args()
            if "-c:v" not in gpu_args:
                cmd.extend(gpu_args)

        cmd.extend([
            "-filter_complex", filter_complex,
        ])

        if use_gpu and self._gpu_available:
            if "-c:v" not in self.get_ffmpeg_gpu_args():
                cmd.extend(["-c:v", "libx264"])

        cmd.extend([
            "-preset", self.get_optimized_preset(speed),
            "-crf", "18",
            "-c:a", "aac",
            "-b:a", "192k",
            str(output_path)
        ])

        logger.info(f"Fast compositing video (GPU: {use_gpu and self._gpu_available})")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            raise RuntimeError(f"Failed to composite video: {result.stderr}")

        logger.info(f"Composited video saved: {output_path}")
        return output_path

    def get_processing_stats(self) -> Dict[str, any]:
        """Get current processing stats and capabilities"""
        return {
            "gpu_available": self._gpu_available,
            "gpu_device": self._gpu_device,
            "platform": platform.system(),
            "gpu_acceleration": self._gpu_device != "none",
            "recommended_preset": self.get_optimized_preset("medium"),
        }


# Singleton instance
optimized_video_processor = OptimizedVideoProcessor()
