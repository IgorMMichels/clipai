"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Volume2, VolumeX } from "lucide-react";
import { cn } from "@/lib/utils";

interface WordSegment {
  text: string;
  start_time: number;
  end_time: number;
}

interface VideoSubtitlesProps {
  videoRef: React.RefObject<HTMLVideoElement | null>;
  segments?: WordSegment[];
  showSubtitles?: boolean;
  onToggleSubtitles?: () => void;
}

export function VideoSubtitles({ videoRef, segments, showSubtitles = true, onToggleSubtitles }: VideoSubtitlesProps) {
  const [currentText, setCurrentText] = useState("");
  const [currentTime, setCurrentTime] = useState(0);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleTimeUpdate = () => setCurrentTime(video.currentTime);

    video.addEventListener("timeupdate", handleTimeUpdate);

    return () => {
      video.removeEventListener("timeupdate", handleTimeUpdate);
    };
  }, [videoRef]);

  useEffect(() => {
    if (!segments || segments.length === 0) {
      setCurrentText("");
      return;
    }

    const currentSegment = segments.find(
      (seg) => currentTime >= seg.start_time && currentTime <= seg.end_time
    );

    if (currentSegment) {
      setCurrentText(currentSegment.text);
    } else {
      setCurrentText("");
    }
  }, [currentTime, segments]);

  const handleToggleSubtitles = () => {
    if (onToggleSubtitles) {
      onToggleSubtitles();
    }
  };

  if (!showSubtitles || !segments || segments.length === 0) {
    return (
      <button
        onClick={handleToggleSubtitles}
        className="absolute bottom-20 right-4 z-20 p-2 rounded-lg bg-black/50 hover:bg-black/70 backdrop-blur-sm transition-all duration-200"
      >
        <VolumeX className="h-4 w-4 text-white" />
      </button>
    );
  }

  return (
    <>
      {/* Subtitles Overlay - Positioned over video */}
      <div className="absolute bottom-12 left-0 right-0 z-10 pointer-events-none">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 10 }}
          className="flex justify-center"
        >
          <div className="max-w-[90%] bg-black/70 backdrop-blur-md px-6 py-3 rounded-lg shadow-2xl">
            <p className="text-lg md:text-xl font-medium text-white text-center leading-relaxed drop-shadow-lg">
              {currentText}
            </p>
          </div>
        </motion.div>
      </div>

      {/* Toggle Button */}
      <button
        onClick={handleToggleSubtitles}
        className="absolute bottom-20 right-4 z-20 p-2 rounded-lg bg-black/50 hover:bg-black/70 backdrop-blur-sm transition-all duration-200"
      >
        <Volume2 className="h-4 w-4 text-white" />
      </button>
    </>
  );
}
