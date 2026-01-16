"""
Test Suite for Enhanced Features
Tests multi-modal analysis, scene detection, camera switching, and batch processing
"""
import pytest


class TestEnhancedFeatures:
    """Test enhanced ClipAI features"""

    @pytest.fixture
    def sample_transcription(self):
        """Sample transcription for testing"""
        return {
            "sentences": [
                {"text": "This is amazing!", "start_time": 0.0, "end_time": 2.5, "words": []},
                {"text": "Check this out", "start_time": 2.5, "end_time": 5.0, "words": []},
                {"text": "It's incredible", "start_time": 5.0, "end_time": 7.5, "words": []},
            ],
            "words": [
                {"text": "This", "start_time": 0.0, "end_time": 0.5},
                {"text": "is", "start_time": 0.5, "end_time": 0.8},
                {"text": "amazing", "start_time": 0.8, "end_time": 1.5},
            ],
        }

    def test_enhanced_clip_finder_import(self):
        """Test that enhanced clip finder can be imported"""
        try:
            from services.enhanced_clipper import enhanced_clip_finder_service
            assert enhanced_clip_finder_service.is_available
            print("OK - Enhanced clip finder service loaded")
        except Exception as e:
            pytest.fail(f"Failed to import enhanced clip finder: {e}")

    def test_scene_detection_import(self):
        """Test that scene detection can be imported"""
        try:
            from services.scene_detection import scene_detection_service
            assert scene_detection_service.is_available
            print("OK - Scene detection service loaded")
        except Exception as e:
            pytest.fail(f"Failed to import scene detection: {e}")

    def test_camera_switching_import(self):
        """Test that camera switching can be imported"""
        try:
            from services.camera_switching import camera_switching_service
            assert camera_switching_service.is_available
            print("OK - Camera switching service loaded")
        except Exception as e:
            pytest.fail(f"Failed to import camera switching: {e}")

    def test_enhanced_captions_import(self):
        """Test that enhanced captions can be imported"""
        try:
            from services.enhanced_captions import enhanced_captions_service
            assert enhanced_captions_service is not None
            print("OK - Enhanced captions service loaded")
        except Exception as e:
            pytest.fail(f"Failed to import enhanced captions: {e}")

    def test_optimized_processor_import(self):
        """Test that optimized processor can be imported"""
        try:
            from services.optimized_processor import optimized_video_processor
            assert optimized_video_processor is not None
            stats = optimized_video_processor.get_processing_stats()
            print(f"OK - Optimized processor loaded: GPU={stats['gpu_available']}")
        except Exception as e:
            pytest.fail(f"Failed to import optimized processor: {e}")

    def test_batch_processor_import(self):
        """Test that batch processor can be imported"""
        try:
            from services.batch_processor import batch_processing_service
            assert batch_processing_service is not None
            print("OK - Batch processor service loaded")
        except Exception as e:
            pytest.fail(f"Failed to import batch processor: {e}")

    def test_quality_presets_import(self):
        """Test that quality presets can be imported"""
        try:
            from services.quality_presets import quality_presets_service, QUALITY_PRESETS
            assert quality_presets_service is not None
            assert "tiktok" in QUALITY_PRESETS
            preset = quality_presets_service.get_preset("tiktok")
            assert preset.name == "TikTok"
            print(f"OK - Quality presets loaded: {len(QUALITY_PRESETS)} presets available")
        except Exception as e:
            pytest.fail(f"Failed to import quality presets: {e}")

    def test_services_init(self):
        """Test that services __init__.py includes all enhanced services"""
        try:
            from services import (
                enhanced_clip_finder_service,
                enhanced_captions_service,
                scene_detection_service,
                camera_switching_service,
                optimized_video_processor,
                batch_processing_service,
                quality_presets_service,
                QUALITY_PRESETS,
            )
            print("OK - All enhanced services properly exported")
        except ImportError as e:
            pytest.fail(f"Failed to import enhanced services: {e}")

    def test_caption_styles(self):
        """Test caption style enumeration"""
        from services.enhanced_captions import CaptionStyle
        assert hasattr(CaptionStyle, "VIRAL")
        assert hasattr(CaptionStyle, "KARAOKE")
        assert hasattr(CaptionStyle, "GRADIENT")
        assert hasattr(CaptionStyle, "NEON")
        assert hasattr(CaptionStyle, "BOUNCE")
        assert hasattr(CaptionStyle, "WAVE")
        assert hasattr(CaptionStyle, "GLOW")
        print(f"OK - Caption styles: {len(CaptionStyle)} styles available")

    def test_quality_presets_complete(self):
        """Test that all quality presets are defined"""
        from services.quality_presets import QUALITY_PRESETS
        required_presets = [
            "tiktok",
            "instagram_reels",
            "youtube_shorts",
            "youtube_standard",
            "twitter",
            "linkedin",
            "facebook",
            "high_quality",
            "balanced",
            "fast",
        ]
        for preset_id in required_presets:
            assert preset_id in QUALITY_PRESETS, f"Missing preset: {preset_id}"
        print(f"OK - All {len(required_presets)} quality presets available")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
