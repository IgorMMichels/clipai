"""
Facecam Detection Service
Detects face regions in videos for picture-in-picture layouts
Uses OpenCV and MediaPipe for face detection
"""
import logging
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Try to import mediapipe for better face detection
MEDIAPIPE_AVAILABLE = False
mp_face_detection = None
try:
    import mediapipe as mp
    mp_face_detection = mp.solutions.face_detection  # type: ignore
    MEDIAPIPE_AVAILABLE = True
    logger.info("MediaPipe face detection available")
except Exception as e:
    logger.warning(f"MediaPipe not available: {e}. Using OpenCV cascade.")


class FacecamDetector:
    """Detects facecam regions in videos"""
    
    def __init__(self):
        self._face_cascade = None
        self._mp_detector = None
    
    def _get_opencv_cascade(self):
        """Lazy load OpenCV cascade classifier"""
        if self._face_cascade is None:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'  # type: ignore
            self._face_cascade = cv2.CascadeClassifier(cascade_path)
        return self._face_cascade
    
    def _get_mediapipe_detector(self):
        """Lazy load MediaPipe detector"""
        if self._mp_detector is None and MEDIAPIPE_AVAILABLE and mp_face_detection is not None:
            self._mp_detector = mp_face_detection.FaceDetection(
                model_selection=1,  # Full range model
                min_detection_confidence=0.5
            )
        return self._mp_detector
    
    def detect_facecam_region(
        self,
        video_path: str | Path,
        sample_frames: int = 10,
        min_face_area_ratio: float = 0.02,
    ) -> Optional[Dict]:
        """
        Detect the facecam region in a video
        
        Args:
            video_path: Path to video file
            sample_frames: Number of frames to sample for detection
            min_face_area_ratio: Minimum face area as ratio of frame
            
        Returns:
            Dict with facecam region info or None if not detected
        """
        video_path = Path(video_path)
        
        if not video_path.exists():
            logger.error(f"Video file not found: {video_path}")
            return None
        
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            logger.error(f"Could not open video: {video_path}")
            return None
        
        try:
            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            if total_frames <= 0:
                logger.warning("Could not determine frame count")
                total_frames = 1000
            
            # Sample frames evenly across video
            frame_indices = np.linspace(0, total_frames - 1, sample_frames, dtype=int)
            
            all_faces = []
            
            for frame_idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                
                if not ret:
                    continue
                
                faces = self._detect_faces_in_frame(frame)
                all_faces.extend(faces)
            
            if not all_faces:
                logger.info("No faces detected in video")
                return None
            
            # Find the most consistent face region (likely facecam)
            facecam_region = self._find_consistent_region(
                all_faces, 
                frame_width, 
                frame_height,
                min_face_area_ratio
            )
            
            if facecam_region:
                logger.info(f"Detected facecam region: {facecam_region}")
                return {
                    "x": facecam_region[0],
                    "y": facecam_region[1],
                    "width": facecam_region[2],
                    "height": facecam_region[3],
                    "frame_width": frame_width,
                    "frame_height": frame_height,
                    "confidence": 0.85,
                    "is_corner": self._is_corner_position(
                        facecam_region, frame_width, frame_height
                    ),
                }
            
            return None
            
        finally:
            cap.release()
    
    def _detect_faces_in_frame(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect faces in a single frame"""
        faces = []
        
        if MEDIAPIPE_AVAILABLE:
            detector = self._get_mediapipe_detector()
            if detector:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = detector.process(rgb_frame)
                
                if results.detections:
                    h, w = frame.shape[:2]
                    for detection in results.detections:
                        bbox = detection.location_data.relative_bounding_box
                        x = int(bbox.xmin * w)
                        y = int(bbox.ymin * h)
                        width = int(bbox.width * w)
                        height = int(bbox.height * h)
                        faces.append((x, y, width, height))
        
        # Fallback to OpenCV if no faces found or MediaPipe not available
        if not faces:
            cascade = self._get_opencv_cascade()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            detected = cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            faces = [(x, y, w, h) for (x, y, w, h) in detected]
        
        return faces
    
    def _find_consistent_region(
        self,
        faces: List[Tuple[int, int, int, int]],
        frame_width: int,
        frame_height: int,
        min_area_ratio: float,
    ) -> Optional[Tuple[int, int, int, int]]:
        """Find the most consistent face region (likely a fixed facecam)"""
        if not faces:
            return None
        
        # Group faces by approximate position (within 20% of frame)
        tolerance = 0.2
        groups = []
        
        for face in faces:
            x, y, w, h = face
            center_x = x + w / 2
            center_y = y + h / 2
            
            # Check area ratio
            area_ratio = (w * h) / (frame_width * frame_height)
            if area_ratio < min_area_ratio:
                continue
            
            # Find matching group
            matched = False
            for group in groups:
                avg_cx = sum(f[0] + f[2]/2 for f in group) / len(group)
                avg_cy = sum(f[1] + f[3]/2 for f in group) / len(group)
                
                if (abs(center_x - avg_cx) < frame_width * tolerance and
                    abs(center_y - avg_cy) < frame_height * tolerance):
                    group.append(face)
                    matched = True
                    break
            
            if not matched:
                groups.append([face])
        
        if not groups:
            return None
        
        # Find the largest group (most consistent position)
        largest_group = max(groups, key=len)
        
        if len(largest_group) < 2:
            # Not enough consistent detections
            return None
        
        # Calculate average bounding box with some padding
        avg_x = int(np.mean([f[0] for f in largest_group]))
        avg_y = int(np.mean([f[1] for f in largest_group]))
        avg_w = int(np.mean([f[2] for f in largest_group]))
        avg_h = int(np.mean([f[3] for f in largest_group]))
        
        # Add padding (50% around face for facecam region)
        pad_x = int(avg_w * 0.5)
        pad_y = int(avg_h * 0.5)
        
        region_x = max(0, avg_x - pad_x)
        region_y = max(0, avg_y - pad_y)
        region_w = min(frame_width - region_x, avg_w + 2 * pad_x)
        region_h = min(frame_height - region_y, avg_h + 2 * pad_y)
        
        return (region_x, region_y, region_w, region_h)
    
    def _is_corner_position(
        self,
        region: Tuple[int, int, int, int],
        frame_width: int,
        frame_height: int,
    ) -> str:
        """Determine if region is in a corner (typical for facecam)"""
        x, y, w, h = region
        center_x = x + w / 2
        center_y = y + h / 2
        
        threshold = 0.35
        
        is_left = center_x < frame_width * threshold
        is_right = center_x > frame_width * (1 - threshold)
        is_top = center_y < frame_height * threshold
        is_bottom = center_y > frame_height * (1 - threshold)
        
        if is_top and is_left:
            return "top-left"
        elif is_top and is_right:
            return "top-right"
        elif is_bottom and is_left:
            return "bottom-left"
        elif is_bottom and is_right:
            return "bottom-right"
        else:
            return "center"


# Singleton instance
facecam_detector = FacecamDetector()
