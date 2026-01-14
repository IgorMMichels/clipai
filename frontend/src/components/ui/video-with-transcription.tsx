"use client";

import { useRef, useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import { VideoSubtitles } from "./video-subtitles";

interface WordSegment {
  text: string;
  start_time: number;
  end_time: number;
}

interface VideoWithTranscriptionProps {
  videoSrc: string;
  transcript?: string;
  wordSegments?: WordSegment[];
  showTranscription?: boolean;
  onToggleTranscription?: () => void;
  autoPlay?: boolean;
  loop?: boolean;
  controls?: boolean;
  className?: string;
  style?: React.CSSProperties;
  videoRef?: React.RefObject<HTMLVideoElement | null>;
  onVideoEnd?: () => void;
}

export function VideoWithTranscription({
  videoSrc,
  transcript,
  wordSegments,
  showTranscription = true,
  onToggleTranscription,
  autoPlay = true,
  loop = true,
  controls = true,
  className,
  style,
  videoRef: externalVideoRef,
  onVideoEnd,
}: VideoWithTranscriptionProps) {
  const internalVideoRef = useRef<HTMLVideoElement>(null);
  const videoRef = externalVideoRef || internalVideoRef;
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);
    const handleEnded = () => {
      setIsPlaying(false);
      onVideoEnd?.();
    };

    video.addEventListener("play", handlePlay);
    video.addEventListener("pause", handlePause);
    video.addEventListener("ended", handleEnded);

    return () => {
      video.removeEventListener("play", handlePlay);
      video.removeEventListener("pause", handlePause);
      video.removeEventListener("ended", handleEnded);
    };
  }, [videoRef, onVideoEnd]);

  return (
    <div className={cn("relative bg-black overflow-hidden", className)} style={style}>
      {/* Video Element */}
      <video
        ref={videoRef}
        src={videoSrc}
        autoPlay={autoPlay}
        loop={loop}
        controls={controls}
        playsInline
        className="h-full w-full object-contain"
      />

      {/* Subtitles Overlay */}
      {wordSegments && wordSegments.length > 0 ? (
        <VideoSubtitles
          videoRef={videoRef}
          segments={wordSegments}
          showSubtitles={showTranscription}
          onToggleSubtitles={onToggleTranscription}
        />
      ) : transcript && (
        <div className="absolute bottom-12 left-0 right-0 z-10 pointer-events-none">
          <div className="flex justify-center px-4">
            <div className="max-w-[90%] bg-black/70 backdrop-blur-md px-6 py-3 rounded-lg shadow-2xl">
              <p className="text-lg md:text-xl font-medium text-white text-center leading-relaxed drop-shadow-lg">
                {transcript}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
