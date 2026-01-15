"""
Enhanced Clip Finding Service with Multi-Modal Analysis
Finds optimal clips using semantic analysis, audio energy, visual changes, and heuristic virality scoring.
"""
import logging
import uuid
from typing import List, Dict, Any, Optional
import numpy as np
import cv2
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer, util
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

try:
    import librosa
    import librosa.display
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False

logger = logging.getLogger(__name__)


class EnhancedClipFinderService:
    """Service for finding clips using multi-modal analysis"""

    def __init__(self):
        # Enhanced viral keywords with multi-language support
        self.viral_keywords = {
            # English
            "amazing": 1.5, "incredible": 1.5, "wow": 2.0, "secret": 1.8,
            "hack": 1.5, "money": 1.2, "viral": 1.5, "crazy": 1.4,
            "best": 1.2, "worst": 1.2, "never": 1.2, "always": 1.2,
            "life hack": 2.0, "tutorial": 1.3, "how to": 1.3,
            "omg": 2.0, "lol": 1.5, "funny": 1.2, "scary": 1.3,
            "love": 1.2, "hate": 1.2, "stop": 1.3, "wait": 1.4,
            "cool": 1.2, "insane": 1.4, "unbelievable": 1.5,
            "mind-blowing": 2.0, "game-changer": 1.8, "must-watch": 1.6,

            # Portuguese
            "incrível": 1.5, "uau": 2.0, "segredo": 1.8,
            "hack": 1.5, "dinheiro": 1.2, "viral": 1.5, "loucura": 1.4,
            "melhor": 1.2, "pior": 1.2, "nunca": 1.2, "sempre": 1.2,
            "tutorial": 1.3, "como fazer": 1.3,
            "nossa": 1.5, "engraçado": 1.2, "assustador": 1.3,
            "amor": 1.2, "ódio": 1.2, "pare": 1.3, "espera": 1.4,
            "legal": 1.2, "top": 1.3, "incrivel": 1.5, "louco": 1.4,

            # Spanish
            "increíble": 1.5, "guau": 2.0, "secreto": 1.8,
            "mejor": 1.2, "peor": 1.2, "nunca": 1.2, "siempre": 1.2,
            "asombroso": 1.5, "gracioso": 1.2, "amor": 1.2, "espera": 1.4,
        }

        # Emotional words for sentiment analysis
        self.positive_words = {
            "good", "great", "awesome", "excellent", "happy", "joy", "success", "win", "beautiful",
            "bom", "ótimo", "maravilhoso", "excelente", "feliz", "alegria", "sucesso", "ganhar", "lindo",
            "bueno", "genial", "increíble", "hermoso", "éxito",
        }
        self.negative_words = {
            "bad", "terrible", "awful", "sad", "fail", "loss", "ugly", "pain", "death", "danger",
            "ruim", "terrível", "triste", "falha", "perda", "feio", "dor", "morte", "perigo",
            "malo", "terrible", "triste", "pérdida", "muerte", "peligro",
        }

        # Semantic Search Initialization
        self.model = None
        self.viral_embeddings = None
        self.use_semantic = HAS_TRANSFORMERS

        if self.use_semantic:
            try:
                logger.info("Loading SentenceTransformer model...")
                self.model = SentenceTransformer('all-MiniLM-L6-v2')

                # Expanded viral concepts for semantic matching
                self.viral_concepts = [
                    "This is amazing and incredible",
                    "A secret life hack that changes everything",
                    "Shocking truth revealed",
                    "Hilarious funny moment",
                    "Deep emotional story",
                    "Motivational success advice",
                    "Unexpected plot twist",
                    "Very dangerous situation",
                    "Unbelievable fact",
                    "How to make money fast",
                    "Mind-blowing discovery",
                    "Game-changing technology",
                    "Must-watch viral content",
                    "Insane trick that works",
                    "Never seen before",
                    "This will change your life",
                    "Stop what you're doing",
                    "Wait for it...",
                    "Best moment ever",
                ]
                self.viral_embeddings = self.model.encode(self.viral_concepts, convert_to_tensor=True)
                logger.info("SentenceTransformer model loaded.")
            except Exception as e:
                logger.error(f"Failed to load SentenceTransformer: {e}")
                self.use_semantic = False

    @property
    def is_available(self) -> bool:
        return True

    def find_clips(
        self,
        transcription_obj: Dict[str, Any],
        video_path: Optional[Path] = None,
        min_duration: float = 30.0,
        max_duration: float = 60.0,
        use_audio_analysis: bool = True,
        use_visual_analysis: bool = True,
    ) -> List[dict]:
        """
        Find clips using multi-modal analysis (text, audio, visual)

        Args:
            transcription_obj: Transcription dictionary with words/sentences
            video_path: Path to video file for audio/visual analysis
            min_duration: Minimum clip duration
            max_duration: Maximum clip duration
            use_audio_analysis: Whether to analyze audio energy
            use_visual_analysis: Whether to analyze visual changes

        Returns:
            List of clips with virality scores
        """
        logger.info("Finding clips using Enhanced Multi-Modal engine...")

        sentences = transcription_obj.get("sentences", [])
        if not sentences:
            logger.warning("No sentences found in transcription. Returning empty list.")
            return []

        # Pre-calculate semantic scores
        sentence_semantic_scores = []
        if self.use_semantic and self.model:
            try:
                sentence_texts = [s["text"] for s in sentences]
                embeddings = self.model.encode(sentence_texts, convert_to_tensor=True)
                cosine_scores = util.cos_sim(embeddings, self.viral_embeddings)
                max_scores = cosine_scores.max(dim=1).values.cpu().numpy()
                sentence_semantic_scores = max_scores.tolist()
            except Exception as e:
                logger.error(f"Error calculating semantic scores: {e}")
                sentence_semantic_scores = [0.0] * len(sentences)
        else:
            sentence_semantic_scores = [0.0] * len(sentences)

        # Analyze audio energy if available
        audio_energy_scores = []
        if use_audio_analysis and video_path and HAS_LIBROSA:
            audio_energy_scores = self._analyze_audio_energy(video_path, len(sentences))
        else:
            audio_energy_scores = [0.0] * len(sentences)

        # Analyze visual changes if available
        visual_change_scores = []
        if use_visual_analysis and video_path:
            visual_change_scores = self._analyze_visual_changes(video_path, len(sentences))
        else:
            visual_change_scores = [0.0] * len(sentences)

        clips = []

        # Sliding window approach
        i = 0
        while i < len(sentences):
            current_duration = 0.0
            start_time = sentences[i]["start_time"]
            start_char = sentences[i].get("start_char", 0)

            # Look ahead to build a clip
            j = i
            best_clip_end_idx = -1

            while j < len(sentences):
                sent = sentences[j]
                current_duration = sent["end_time"] - start_time

                if current_duration < min_duration:
                    j += 1
                    continue

                if current_duration > max_duration:
                    break

                best_clip_end_idx = j
                j += 1

            if best_clip_end_idx != -1:
                # Construct clip
                end_sentence = sentences[best_clip_end_idx]
                end_time = end_sentence["end_time"]
                duration = end_time - start_time

                # Extract text
                clip_sentences = sentences[i:best_clip_end_idx + 1]
                transcript = " ".join([s["text"] for s in clip_sentences])

                # Calculate scores
                semantic_score = float(np.mean(sentence_semantic_scores[i:best_clip_end_idx + 1])) * 100.0 if self.use_semantic else 0.0
                heuristic_score = self._calculate_heuristic_score(transcript, duration)

                # Audio score (average energy in clip)
                audio_score = float(np.mean(audio_energy_scores[i:best_clip_end_idx + 1])) * 100.0 if audio_energy_scores else 0.0

                # Visual score (average visual changes in clip)
                visual_score = float(np.mean(visual_change_scores[i:best_clip_end_idx + 1])) * 100.0 if visual_change_scores else 0.0

                # Weighted Total Score
                # 40% Semantic, 25% Heuristic, 20% Audio, 15% Visual
                total_score = (
                    (semantic_score * 0.40) +
                    (heuristic_score * 0.25) +
                    (audio_score * 0.20) +
                    (visual_score * 0.15)
                )

                clips.append({
                    "id": str(uuid.uuid4()),
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration": duration,
                    "start_char": start_char,
                    "end_char": end_sentence.get("end_char", 0),
                    "transcript": transcript,
                    "score": min(99.9, total_score),
                    "semantic_score": semantic_score,
                    "heuristic_score": heuristic_score,
                    "audio_score": audio_score,
                    "visual_score": visual_score,
                    "words": [
                        word for word in (transcription_obj.get("words", []))
                        if word["start_time"] >= start_time and word["end_time"] <= end_time
                    ]
                })

                # Move window
                advance = max(1, (best_clip_end_idx - i) // 2)
                i += advance
            else:
                i += 1

        # Sort by score descending
        clips.sort(key=lambda x: x["score"], reverse=True)

        final_clips = self._remove_overlaps(clips)

        logger.info(f"Found {len(final_clips)} clips with multi-modal analysis.")
        return final_clips[:10]

    def _calculate_heuristic_score(self, text: str, duration: float) -> float:
        """Calculate virality score (0-100)"""
        base_score = 70.0
        text_lower = text.lower()

        # Keyword bonus
        keyword_score = 0.0
        for word, multiplier in self.viral_keywords.items():
            if word in text_lower:
                keyword_score += 5.0 * multiplier

        keyword_score = min(25.0, keyword_score)

        # Pace bonus (words per second)
        word_count = len(text.split())
        wps = word_count / duration if duration > 0 else 0
        pace_score = 0.0
        if wps > 2.5:  # Fast talker
            pace_score = 5.0
        elif wps > 2.0:
            pace_score = 3.0

        # Sentiment/Emotion Bonus
        sentiment_score = 0.0
        words = set(text_lower.split())
        pos_hits = len(words.intersection(self.positive_words))
        neg_hits = len(words.intersection(self.negative_words))

        if pos_hits > 0 or neg_hits > 0:
            sentiment_score += min(5.0, (pos_hits + neg_hits) * 2.0)

        # Intensity (CAPS and Exclamations)
        exc_count = text.count("!")
        if exc_count > 0:
            sentiment_score += min(3.0, exc_count * 1.0)

        caps_words = [w for w in text.split() if w.isupper() and len(w) > 2]
        if len(caps_words) > 0:
            sentiment_score += min(3.0, len(caps_words) * 1.0)

        total_score = base_score + keyword_score + pace_score + sentiment_score
        return min(99.9, total_score)

    def _analyze_audio_energy(self, video_path: Path, num_segments: int) -> List[float]:
        """Analyze audio energy for exciting moments"""
        try:
            logger.info("Analyzing audio energy...")
            # Extract audio using librosa
            y, sr = librosa.load(str(video_path), sr=22050)

            # Calculate RMS energy
            frame_length = 2048
            hop_length = 512
            rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]

            # Normalize to 0-1
            rms_norm = (rms - rms.min()) / (rms.max() - rms.min() + 1e-8)

            # Segment the audio energy based on transcription timing
            video_duration = librosa.get_duration(y=y, sr=sr)
            energy_per_sentence = []

            for i in range(num_segments):
                # Approximate time per sentence
                start_time = (i / num_segments) * video_duration
                end_time = ((i + 1) / num_segments) * video_duration

                # Convert to sample indices
                start_idx = int(start_time * sr / hop_length)
                end_idx = int(end_time * sr / hop_length)

                if start_idx < len(rms_norm) and end_idx <= len(rms_norm):
                    avg_energy = np.mean(rms_norm[start_idx:end_idx])
                    energy_per_sentence.append(avg_energy)
                else:
                    energy_per_sentence.append(0.5)  # Default middle energy

            logger.info(f"Audio energy analysis complete: {len(energy_per_sentence)} segments")
            return energy_per_sentence

        except Exception as e:
            logger.error(f"Audio analysis failed: {e}")
            return [0.5] * num_segments

    def _analyze_visual_changes(self, video_path: Path, num_segments: int) -> List[float]:
        """Analyze visual changes (scene cuts, motion)"""
        try:
            logger.info("Analyzing visual changes...")
            cap = cv2.VideoCapture(str(video_path))

            if not cap.isOpened():
                logger.warning(f"Could not open video for visual analysis: {video_path}")
                return [0.5] * num_segments

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)

            if total_frames <= 0 or fps <= 0:
                cap.release()
                return [0.5] * num_segments

            # Sample frames (every 1 second)
            step_frames = int(fps)
            if step_frames < 1:
                step_frames = 1

            frames = []
            prev_frame = None

            for i in range(0, total_frames, step_frames):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()

                if not ret:
                    continue

                # Resize for faster processing
                frame_small = cv2.resize(frame, (320, 240))

                # Convert to grayscale
                gray = cv2.cvtColor(frame_small, cv2.COLOR_BGR2GRAY)

                frames.append(gray)

                prev_frame = gray

            cap.release()

            if len(frames) < 2:
                return [0.5] * num_segments

            # Calculate frame differences
            changes = []
            for i in range(1, len(frames)):
                diff = cv2.absdiff(frames[i-1], frames[i])
                change_score = np.mean(diff) / 255.0  # Normalize 0-1
                changes.append(change_score)

            # Segment the changes
            changes_per_sentence = []
            frames_per_segment = len(changes) / num_segments if num_segments > 0 else 1

            for i in range(num_segments):
                start_idx = int(i * frames_per_segment)
                end_idx = int((i + 1) * frames_per_segment)

                if start_idx < len(changes) and end_idx <= len(changes):
                    avg_change = np.mean(changes[start_idx:end_idx])
                    changes_per_sentence.append(avg_change)
                else:
                    changes_per_sentence.append(0.5)

            logger.info(f"Visual analysis complete: {len(changes_per_sentence)} segments")
            return changes_per_sentence

        except Exception as e:
            logger.error(f"Visual analysis failed: {e}")
            return [0.5] * num_segments

    def _remove_overlaps(self, clips: List[dict]) -> List[dict]:
        """Remove clips that overlap significantly, keeping higher scored ones"""
        if not clips:
            return []

        kept_clips = []
        clips = sorted(clips, key=lambda x: x["score"], reverse=True)

        for clip in clips:
            is_overlap = False
            for kept in kept_clips:
                start = max(clip["start_time"], kept["start_time"])
                end = min(clip["end_time"], kept["end_time"])
                overlap = max(0, end - start)

                min_dur = min(clip["duration"], kept["duration"])
                if overlap > (0.3 * min_dur):
                    is_overlap = True
                    break

            if not is_overlap:
                kept_clips.append(clip)

        return kept_clips


# Singleton instance
enhanced_clip_finder_service = EnhancedClipFinderService()
