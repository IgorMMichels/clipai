"""
Smart Camera Switching Service
Analyzes video to detect different camera angles and creates optimal switching points
"""
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class CameraSwitchingService:
    """Service for intelligent camera switching between spectator and gameplay"""

    def __init__(self):
        pass

    @property
    def is_available(self) -> bool:
        return True

    def detect_camera_views(
        self,
        video_path: Path,
        sample_interval: float = 2.0,  # Sample every 2 seconds
        min_face_size: float = 0.03,  # Minimum face size as ratio of frame
    ) -> List[Dict[str, any]]:
        """
        Detect different camera views (facecam vs gameplay)

        Args:
            video_path: Path to video file
            sample_interval: Seconds between frame samples
            min_face_size: Minimum face size ratio for facecam detection

        Returns:
            List of camera view segments
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
            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            if fps <= 0 or total_frames <= 0:
                logger.warning("Could not determine video FPS or frame count")
                return []

            # Load face detector
            try:
                face_cascade = cv2.CascadeClassifier(
                    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                )
            except:
                logger.warning("Could not load face cascade")
                return []

            sample_step = int(sample_interval * fps)
            if sample_step < 1:
                sample_step = 1

            camera_views = []
            current_view = None
            current_start_time = 0.0

            frame_idx = 0
            while frame_idx < total_frames:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()

                if not ret:
                    break

                # Analyze frame
                view_type = self._classify_camera_view(
                    frame, face_cascade, frame_width, frame_height, min_face_size
                )

                # Detect view change
                if view_type != current_view:
                    # End previous segment
                    if current_view is not None:
                        camera_views.append({
                            "view_type": current_view,
                            "start_time": current_start_time,
                            "end_time": frame_idx / fps,
                            "duration": (frame_idx / fps) - current_start_time,
                            "confidence": self._get_view_confidence(frame, view_type),
                        })

                    # Start new segment
                    current_view = view_type
                    current_start_time = frame_idx / fps

                frame_idx += sample_step

            # Add final segment
            if current_view is not None:
                camera_views.append({
                    "view_type": current_view,
                    "start_time": current_start_time,
                    "end_time": total_frames / fps,
                    "duration": (total_frames / fps) - current_start_time,
                    "confidence": 1.0,
                })

            cap.release()

            # Post-process: merge short segments and smooth transitions
            camera_views = self._post_process_camera_views(camera_views)

            logger.info(f"Detected {len(camera_views)} camera view segments")
            return camera_views

        except Exception as e:
            logger.error(f"Error detecting camera views: {e}")
            cap.release()
            return []

    def _classify_camera_view(
        self,
        frame: np.ndarray,
        face_cascade,
        frame_width: int,
        frame_height: int,
        min_face_size: float,
    ) -> str:
        """
        Classify the current camera view

        Returns:
            'facecam', 'gameplay', or 'unknown'
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)

        if len(faces) > 0:
            # Check if there's a significant face (likely facecam)
            for (x, y, w, h) in faces:
                face_area = w * h
                frame_area = frame_width * frame_height
                face_ratio = face_area / frame_area

                if face_ratio >= min_face_size:
                    return "facecam"

        # No significant face detected - check for gameplay characteristics
        # High contrast, fast motion, colorful = likely gameplay
        brightness = np.mean(gray) / 255.0
        contrast = np.std(gray) / 128.0

        # Gameplay usually has higher contrast
        if contrast > 0.3:
            return "gameplay"

        # Default to unknown
        return "unknown"

    def _get_view_confidence(self, frame: np.ndarray, view_type: str) -> float:
        """Calculate confidence score for view classification"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if view_type == "facecam":
            # High confidence if there are clear face features
            # This would be enhanced with better face detection
            return 0.8

        elif view_type == "gameplay":
            # Higher confidence if high contrast
            contrast = np.std(gray) / 128.0
            return min(1.0, 0.5 + contrast)

        else:
            return 0.5

    def _post_process_camera_views(
        self,
        camera_views: List[Dict[str, any]],
        min_duration: float = 1.0,
    ) -> List[Dict[str, any]]:
        """
        Post-process camera views to merge short segments and smooth transitions

        Args:
            camera_views: Raw camera view segments
            min_duration: Minimum duration for a view segment

        Returns:
            Processed camera view segments
        """
        if not camera_views:
            return []

        # Merge short segments into neighboring longer segments
        processed_views = []

        for view in camera_views:
            if view["duration"] < min_duration:
                # Too short - merge with previous or next
                if processed_views:
                    last_view = processed_views[-1]
                    # Extend previous view
                    last_view["end_time"] = view["end_time"]
                    last_view["duration"] += view["duration"]
                else:
                    # No previous view, keep as is
                    processed_views.append(view.copy())
            else:
                processed_views.append(view.copy())

        # Smooth transitions between views
        # Add transition buffer times
        transition_buffer = 0.5  # 0.5 second buffer

        for i in range(len(processed_views) - 1):
            current = processed_views[i]
            next_view = processed_views[i + 1]

            # Adjust start/end times with buffer
            current["transition_time"] = current["end_time"] + transition_buffer

        return processed_views

    def find_optimal_switching_points(
        self,
        camera_views: List[Dict[str, any]],
        clip_start: float,
        clip_end: float,
        preferred_switch_interval: float = 5.0,
    ) -> List[Dict[str, float]]:
        """
        Find optimal camera switching points within a clip

        Args:
            camera_views: Camera view segments
            clip_start: Start time of clip
            clip_end: End time of clip
            preferred_switch_interval: Preferred time between switches

        Returns:
            List of recommended switch points
        """
        # Filter views within clip range
        clip_views = [
            v for v in camera_views
            if v["start_time"] < clip_end and v["end_time"] > clip_start
        ]

        switch_points = []

        # Find view boundaries
        for view in clip_views:
            # Start of this view (if within clip)
            if view["start_time"] > clip_start:
                switch_points.append({
                    "time": view["start_time"],
                    "type": "switch_to_" + view["view_type"],
                    "confidence": view["confidence"],
                })

            # End of this view (if within clip)
            if view["end_time"] < clip_end:
                switch_points.append({
                    "time": view["end_time"],
                    "type": "switch_from_" + view["view_type"],
                    "confidence": view["confidence"],
                })

        # Add evenly spaced switches if too few
        if len(switch_points) < (clip_end - clip_start) / preferred_switch_interval:
            num_switches = int((clip_end - clip_start) / preferred_switch_interval)
            for i in range(1, num_switches + 1):
                t = clip_start + (i * preferred_switch_interval)
                if t < clip_end:
                    switch_points.append({
                        "time": t,
                        "type": "timed_switch",
                        "confidence": 0.7,
                    })

        # Sort by time and deduplicate
        switch_points = sorted(switch_points, key=lambda x: x["time"])

        # Remove duplicates (within 0.5s)
        filtered_points = []
        for point in switch_points:
            if not filtered_points:
                filtered_points.append(point)
            else:
                last_point = filtered_points[-1]
                if abs(point["time"] - last_point["time"]) > 0.5:
                    filtered_points.append(point)

        # Filter to clip range
        filtered_points = [
            p for p in filtered_points
            if clip_start < p["time"] < clip_end
        ]

        return filtered_points

    def generate_switching_timeline(
        self,
        camera_views: List[Dict[str, any]],
        transcription_words: List[Dict[str, any]],
        clip_duration: float,
    ) -> List[Dict[str, any]]:
        """
        Generate a timeline with optimal camera switches based on content

        Args:
            camera_views: Camera view segments
            transcription_words: Word-level transcription
            clip_duration: Total duration of clip

        Returns:
            Timeline with camera switches and highlights
        """
        timeline = []

        # Add camera view segments
        for view in camera_views:
            timeline.append({
                "time": view["start_time"],
                "type": "camera_change",
                "view_type": view["view_type"],
                "duration": view["duration"],
                "confidence": view["confidence"],
            })

        # Find interesting moments in transcription
        interesting_keywords = ["wow", "incredible", "amazing", "check this", "look", "secret"]

        for word in transcription_words:
            word_text = word.get("text", "").lower()

            if any(keyword in word_text for keyword in interesting_keywords):
                timeline.append({
                    "time": word["start_time"],
                    "type": "highlight",
                    "text": word["text"],
                    "reason": "interesting_keyword",
                })

        # Sort timeline by time
        timeline = sorted(timeline, key=lambda x: x["time"])

        # Filter to clip duration
        timeline = [t for t in timeline if t["time"] < clip_duration]

        return timeline


# Singleton instance
camera_switching_service = CameraSwitchingService()
