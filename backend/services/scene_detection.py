"""
Scene Detection Service
Detects scene changes and transitions in videos for intelligent cutting
"""
import logging
from pathlib import Path
from typing import List, Dict, Tuple
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class SceneDetectionService:
    """Service for detecting scene changes and transitions"""

    def __init__(self):
        pass

    @property
    def is_available(self) -> bool:
        return True

    def detect_scenes(
        self,
        video_path: Path,
        threshold: float = 0.3,
        min_scene_duration: float = 2.0,
    ) -> List[Dict[str, float]]:
        """
        Detect scene changes in a video

        Args:
            video_path: Path to video file
            threshold: Change threshold (0.0-1.0, lower = more sensitive)
            min_scene_duration: Minimum duration between scene changes (seconds)

        Returns:
            List of scene boundaries with timestamps
        """
        video_path = Path(video_path)

        if not video_path.exists():
            logger.error(f"Video file not found: {video_path}")
            return []

        cap = cv2.VideoCapture(str(video_path))

        if not cap.isOpened():
            logger.error(f"Could not open video: {video_path}")
            return []

        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            if fps <= 0 or total_frames <= 0:
                logger.warning("Could not determine video FPS or frame count")
                return []

            min_frame_gap = int(min_scene_duration * fps)

            # Read first frame
            ret, prev_frame = cap.read()
            if not ret:
                return []

            prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            prev_gray = cv2.resize(prev_gray, (320, 240))  # Resize for speed

            scenes = [{"time": 0.0, "frame": 0, "type": "start"}]
            last_scene_frame = 0

            frame_idx = 1
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.resize(gray, (320, 240))

                # Calculate frame difference
                diff = cv2.absdiff(prev_gray, gray)
                change_score = np.mean(diff) / 255.0  # Normalize 0-1

                # Scene change detected
                if change_score > threshold and (frame_idx - last_scene_frame) > min_frame_gap:
                    timestamp = frame_idx / fps
                    scenes.append({
                        "time": timestamp,
                        "frame": frame_idx,
                        "type": "cut",
                        "change_score": change_score
                    })
                    last_scene_frame = frame_idx

                prev_gray = gray
                frame_idx += 1

            # Add end scene
            scenes.append({"time": total_frames / fps, "frame": total_frames, "type": "end"})

            cap.release()
            logger.info(f"Detected {len(scenes)-2} scene changes in video")
            return scenes

        except Exception as e:
            logger.error(f"Error detecting scenes: {e}")
            cap.release()
            return []

    def find_best_transition_points(
        self,
        scenes: List[Dict[str, float]],
        clip_start: float,
        clip_end: float,
        preferred_duration: float = 5.0,
    ) -> List[float]:
        """
        Find optimal transition points within a clip

        Args:
            scenes: List of scene boundaries
            clip_start: Start time of clip
            clip_end: End time of clip
            preferred_duration: Preferred clip duration for cuts

        Returns:
            List of recommended cut timestamps
        """
        # Find scenes within clip range
        clip_scenes = [
            s for s in scenes
            if clip_start <= s["time"] <= clip_end
        ]

        transition_points = []

        for i in range(len(clip_scenes)):
            current = clip_scenes[i]
            if current["type"] in ["cut", "fade", "dissolve"]:
                transition_points.append(current["time"])

        # Also add evenly spaced points if transitions are sparse
        if len(transition_points) < 3:
            num_points = int((clip_end - clip_start) / preferred_duration)
            for i in range(1, num_points + 1):
                t = clip_start + (i * preferred_duration)
                if t < clip_end:
                    transition_points.append(t)

        # Sort and deduplicate
        transition_points = sorted(list(set(transition_points)))
        transition_points = [t for t in transition_points if clip_start < t < clip_end]

        return transition_points

    def analyze_scene_characteristics(
        self,
        video_path: Path,
        scenes: List[Dict[str, float]],
    ) -> Dict[str, any]:
        """
        Analyze characteristics of each scene

        Returns:
            Dict with scene analysis (brightness, motion, color distribution)
        """
        video_path = Path(video_path)

        if not video_path.exists():
            logger.error(f"Video file not found: {video_path}")
            return {}

        cap = cv2.VideoCapture(str(video_path))

        if not cap.isOpened():
            logger.error(f"Could not open video: {video_path}")
            return {}

        try:
            scene_analysis = []

            for i in range(len(scenes) - 1):
                start_scene = scenes[i]
                end_scene = scenes[i + 1]

                start_time = start_scene["time"]
                end_time = end_scene["time"]

                # Extract a sample frame from the scene
                mid_time = (start_time + end_time) / 2
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_idx = int(mid_time * fps)

                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()

                if not ret:
                    continue

                # Analyze frame characteristics
                analysis = self._analyze_frame(frame)
                analysis["time"] = start_time
                analysis["duration"] = end_time - start_time
                analysis["scene_index"] = i
                scene_analysis.append(analysis)

            cap.release()
            logger.info(f"Analyzed {len(scene_analysis)} scenes")
            return {"scenes": scene_analysis}

        except Exception as e:
            logger.error(f"Error analyzing scenes: {e}")
            cap.release()
            return {}

    def _analyze_frame(self, frame: np.ndarray) -> Dict[str, float]:
        """Analyze frame characteristics"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Brightness (0-1)
        brightness = np.mean(gray) / 255.0

        # Color distribution (HSV)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)

        hue_avg = np.mean(h) / 180.0  # Normalize 0-2 to 0-1
        saturation_avg = np.mean(s) / 255.0

        # Contrast
        contrast = np.std(gray) / 128.0  # Normalize

        # Edge density (indicates detail/motion)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (gray.shape[0] * gray.shape[1])

        return {
            "brightness": brightness,
            "contrast": contrast,
            "hue": hue_avg,
            "saturation": saturation_avg,
            "edge_density": edge_density,
        }


# Singleton instance
scene_detection_service = SceneDetectionService()
