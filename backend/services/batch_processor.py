"""
Batch Processing Service
Process multiple clips in parallel for maximum throughput
"""
import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import settings

logger = logging.getLogger(__name__)


class BatchProcessingService:
    """Service for batch processing multiple clips"""

    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.active_jobs = {}

    async def process_clips_batch(
        self,
        clips_data: List[Dict[str, Any]],
        video_path: Path,
        options: Dict[str, Any],
        progress_callback: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """
        Process multiple clips in parallel

        Args:
            clips_data: List of clips to process
            video_path: Source video path
            options: Processing options (resolution, captions, etc.)
            progress_callback: Optional callback for progress updates

        Returns:
            Batch processing results
        """
        batch_id = str(uuid.uuid4())
        total_clips = len(clips_data)

        logger.info(f"Starting batch processing of {total_clips} clips (batch_id: {batch_id})")

        results = {
            "batch_id": batch_id,
            "total_clips": total_clips,
            "completed": 0,
            "failed": 0,
            "results": [],
            "progress": 0.0,
        }

        # Process clips in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    self._process_single_clip,
                    clip_data,
                    video_path,
                    options,
                    i,
                ): i
                for i, clip_data in enumerate(clips_data)
            }

            # Track progress
            completed_count = 0

            for future in as_completed(futures):
                clip_index = futures[future]
                try:
                    result = future.result()

                    if result["success"]:
                        results["completed"] += 1
                        results["results"].append(result)
                    else:
                        results["failed"] += 1
                        logger.error(f"Clip {clip_index} failed: {result.get('error')}")

                    completed_count += 1

                    # Update progress
                    if progress_callback:
                        progress = (completed_count / total_clips) * 100
                        results["progress"] = progress

                        try:
                            await progress_callback({
                                "batch_id": batch_id,
                                "progress": progress,
                                "completed": completed_count,
                                "failed": results["failed"],
                                "total": total_clips,
                                "current_clip": clip_index,
                            })
                        except Exception as e:
                            logger.warning(f"Progress callback failed: {e}")

                except Exception as e:
                    logger.error(f"Error processing clip {clip_index}: {e}")
                    results["failed"] += 1

        results["progress"] = 100.0
        logger.info(f"Batch processing complete: {results['completed']}/{total_clips} successful")

        return results

    def _process_single_clip(
        self,
        clip_data: Dict[str, Any],
        video_path: Path,
        options: Dict[str, Any],
        clip_index: int,
    ) -> Dict[str, Any]:
        """
        Process a single clip

        Args:
            clip_data: Clip metadata
            video_path: Source video path
            options: Processing options
            clip_index: Index in batch

        Returns:
            Processing result
        """
        try:
            from services import video_editor_service, optimized_video_processor

            clip_id = clip_data.get("id", str(uuid.uuid4()))
            start_time = clip_data.get("start_time", 0)
            end_time = clip_data.get("end_time", 30)
            duration = end_time - start_time

            # Create output directory
            output_dir = settings.OUTPUT_DIR / clip_id[:8]
            output_dir.mkdir(parents=True, exist_ok=True)

            output_path = output_dir / f"clip_{clip_index}.mp4"

            # Get options
            use_gpu = options.get("use_gpu", True)
            speed = options.get("speed", "fast")
            add_captions = options.get("add_captions", False)
            caption_theme = options.get("caption_theme", "viral")
            caption_style = options.get("caption_style", "karaoke")
            quality_preset = options.get("quality_preset", "tiktok")

            # Get quality preset settings
            from services.quality_presets import quality_presets_service
            preset = quality_presets_service.get_preset(quality_preset)
            preset_args = quality_presets_service.get_ffmpeg_args_from_preset(preset)

            # Step 1: Trim with GPU
            trimmed_path = output_dir / f"trimmed_{clip_index}.mp4"
            optimized_video_processor.fast_trim(
                input_path=video_path,
                output_path=trimmed_path,
                start_time=start_time,
                end_time=end_time,
                use_gpu=use_gpu,
                speed=speed,
            )

            # Step 2: Resize if needed
            if preset.resolution != (1080, 1920):
                resized_path = output_dir / f"resized_{clip_index}.mp4"
                optimized_video_processor.fast_resize(
                    input_path=trimmed_path,
                    output_path=resized_path,
                    width=preset.resolution[0],
                    height=preset.resolution[1],
                    use_gpu=use_gpu,
                    speed=speed,
                )
                working_path = resized_path
            else:
                working_path = trimmed_path

            # Step 3: Add captions if requested
            if add_captions and options.get("words"):
                subtitled_path = output_path / f"subtitled_{clip_index}.mp4"

                from services.enhanced_captions import enhanced_captions_service
                from backend.services.captions import CaptionStyle

                enhanced_captions_service.burn_captions_to_video(
                    video_path=working_path,
                    output_path=subtitled_path,
                    words=options["words"],
                    theme_id=caption_theme,
                    style=CaptionStyle(caption_style),
                    words_per_line=3,
                )
                working_path = subtitled_path

            # Final output path
            final_path = output_path

            # Move to final location
            import shutil
            shutil.move(str(working_path), str(final_path))

            # Cleanup temp files
            if trimmed_path.exists() and trimmed_path != working_path:
                trimmed_path.unlink()

            return {
                "success": True,
                "clip_id": clip_id,
                "clip_index": clip_index,
                "output_path": str(final_path),
                "duration": duration,
                "quality_preset": quality_preset,
                "has_captions": add_captions,
            }

        except Exception as e:
            import traceback
            logger.error(f"Error processing clip {clip_index}: {traceback.format_exc()}")
            return {
                "success": False,
                "clip_id": clip_data.get("id"),
                "clip_index": clip_index,
                "error": str(e),
            }

    def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a batch processing job"""
        return self.active_jobs.get(batch_id)

    def cancel_batch(self, batch_id: str) -> bool:
        """Cancel a batch processing job"""
        if batch_id in self.active_jobs:
            # TODO: Implement cancellation logic
            del self.active_jobs[batch_id]
            logger.info(f"Cancelled batch processing job: {batch_id}")
            return True
        return False


# Singleton instance
batch_processing_service = BatchProcessingService()
