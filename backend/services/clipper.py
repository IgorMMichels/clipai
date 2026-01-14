"""
Clip Finding Service
Finds optimal clips using sentence-based segmentation and heuristic virality scoring.
"""
import logging
import uuid
from typing import List, Dict, Any
import numpy as np
try:
    from sentence_transformers import SentenceTransformer, util
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

logger = logging.getLogger(__name__)

class ClipFinderService:
    """Service for finding clips in transcribed content"""
    
    def __init__(self):
        # Heuristic keywords for virality
        self.viral_keywords = {
            # English
            "amazing": 1.5, "incredible": 1.5, "wow": 2.0, "secret": 1.8,
            "hack": 1.5, "money": 1.2, "viral": 1.5, "crazy": 1.4,
            "best": 1.2, "worst": 1.2, "never": 1.2, "always": 1.2,
            "life hack": 2.0, "tutorial": 1.3, "how to": 1.3,
            "omg": 2.0, "lol": 1.5, "funny": 1.2, "scary": 1.3,
            "love": 1.2, "hate": 1.2, "stop": 1.3, "wait": 1.4,
            "cool": 1.2,
            
            # Portuguese
            "incrível": 1.5, "uau": 2.0, "segredo": 1.8,
            "hack": 1.5, "dinheiro": 1.2, "viral": 1.5, "loucura": 1.4,
            "melhor": 1.2, "pior": 1.2, "nunca": 1.2, "sempre": 1.2,
            "tutorial": 1.3, "como fazer": 1.3,
            "nossa": 1.5, "engraçado": 1.2, "assustador": 1.3,
            "amor": 1.2, "ódio": 1.2, "pare": 1.3, "espera": 1.4,
            "legal": 1.2, "top": 1.3
        }
        
        # Emotional words for sentiment analysis
        self.positive_words = {
            "good", "great", "awesome", "excellent", "happy", "joy", "success", "win", "beautiful",
            "bom", "ótimo", "maravilhoso", "excelente", "feliz", "alegria", "sucesso", "ganhar", "lindo"
        }
        self.negative_words = {
            "bad", "terrible", "awful", "sad", "fail", "loss", "ugly", "pain", "death", "danger",
            "ruim", "terrível", "triste", "falha", "perda", "feio", "dor", "morte", "perigo"
        }

        # Semantic Search Initialization
        self.model = None
        self.viral_embeddings = None
        self.use_semantic = HAS_TRANSFORMERS
        
        if self.use_semantic:
            try:
                logger.info("Loading SentenceTransformer model...")
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                
                # Define viral concepts for semantic matching
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
                    "How to make money fast"
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
        min_duration: float = 30.0,
        max_duration: float = 60.0,
    ) -> List[dict]:
        """
        Find clips from a transcription dictionary.
        Uses a sliding window over sentences to find segments that fit duration constraints
        and maximize 'virality' score (Heuristic + Semantic).
        """
        logger.info("Finding clips using Hybrid (Heuristic + Semantic) engine...")
        
        sentences = transcription_obj.get("sentences", [])
        if not sentences:
            logger.warning("No sentences found in transcription. Returning empty list.")
            return []
            
        # Pre-calculate semantic scores for all sentences if model is available
        sentence_semantic_scores = []
        if self.use_semantic and self.model:
            try:
                sentence_texts = [s["text"] for s in sentences]
                embeddings = self.model.encode(sentence_texts, convert_to_tensor=True)
                # Calculate max similarity to any viral concept for each sentence
                cosine_scores = util.cos_sim(embeddings, self.viral_embeddings)
                # cosine_scores shape: [num_sentences, num_viral_concepts]
                # We take the max score for each sentence across all viral concepts
                max_scores = cosine_scores.max(dim=1).values.cpu().numpy()
                sentence_semantic_scores = max_scores.tolist()
            except Exception as e:
                logger.error(f"Error calculating semantic scores: {e}")
                sentence_semantic_scores = [0.0] * len(sentences)
        else:
             sentence_semantic_scores = [0.0] * len(sentences)

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
                
                # Valid duration window
                best_clip_end_idx = j
                j += 1
            
            if best_clip_end_idx != -1:
                # Construct clip
                end_sentence = sentences[best_clip_end_idx]
                end_time = end_sentence["end_time"]
                duration = end_time - start_time
                
                # Extract text
                clip_sentences = sentences[i : best_clip_end_idx + 1]
                transcript = " ".join([s["text"] for s in clip_sentences])
                
                # Semantic Score: Average of max semantic scores of sentences in clip
                # (Or maybe max? Average seems safer for consistency)
                if self.use_semantic:
                    segment_scores = sentence_semantic_scores[i : best_clip_end_idx + 1]
                    semantic_score = float(np.mean(segment_scores)) * 100.0 # Scale 0-1 to 0-100
                else:
                    semantic_score = 0.0

                # Calculate Heuristic Score
                heuristic_score = self._calculate_heuristic_score(transcript, duration)
                
                # Weighted Total Score
                # 60% Semantic (Real AI), 40% Heuristic
                if self.use_semantic:
                    total_score = (semantic_score * 0.6) + (heuristic_score * 0.4)
                else:
                    total_score = heuristic_score
                
                clips.append({
                    "id": str(uuid.uuid4()),
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration": duration,
                    "start_char": start_char,
                    "end_char": end_sentence.get("end_char", 0),
                    "transcript": transcript,
                    "score": min(99.9, total_score),
                    "semantic_score": semantic_score if self.use_semantic else 0,
                    "heuristic_score": heuristic_score,
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
        
        logger.info(f"Found {len(final_clips)} clips.")
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
        
        # Cap keyword score
        keyword_score = min(25.0, keyword_score)
        
        # Pace bonus (words per second) - faster is usually more energetic
        word_count = len(text.split())
        wps = word_count / duration if duration > 0 else 0
        pace_score = 0.0
        if wps > 2.5: # Fast talker
            pace_score = 5.0
            
        # Sentiment/Emotion Bonus (Robust Heuristic)
        sentiment_score = 0.0
        
        # 1. Check for emotional words
        words = set(text_lower.split())
        pos_hits = len(words.intersection(self.positive_words))
        neg_hits = len(words.intersection(self.negative_words))
        
        if pos_hits > 0 or neg_hits > 0:
            # Emotion is good for virality, whether positive or negative
            sentiment_score += min(5.0, (pos_hits + neg_hits) * 2.0)
            
        # 2. Check for intensity (CAPS and Exclamations)
        # Count exclamation marks
        exc_count = text.count("!")
        if exc_count > 0:
            sentiment_score += min(3.0, exc_count * 1.0)
            
        # Count uppercase words (longer than 2 chars to avoid 'I', 'A')
        caps_words = [w for w in text.split() if w.isupper() and len(w) > 2]
        if len(caps_words) > 0:
             sentiment_score += min(3.0, len(caps_words) * 1.0)
        
        total_score = base_score + keyword_score + pace_score + sentiment_score
        return min(99.9, total_score)

    def _remove_overlaps(self, clips: List[dict]) -> List[dict]:
        """Remove clips that overlap significantly, keeping higher scored ones"""
        if not clips:
            return []
            
        kept_clips = []
        # Clips are already sorted by score desc
        
        for clip in clips:
            is_overlap = False
            for kept in kept_clips:
                # Check intersection
                start = max(clip["start_time"], kept["start_time"])
                end = min(clip["end_time"], kept["end_time"])
                overlap = max(0, end - start)
                
                # If overlap is > 30% of the smaller clip's duration, reject it
                min_dur = min(clip["duration"], kept["duration"])
                if overlap > (0.3 * min_dur):
                    is_overlap = True
                    break
            
            if not is_overlap:
                kept_clips.append(clip)
                
        return kept_clips

# Singleton instance
clip_finder_service = ClipFinderService()
