"use client";

import { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import {
  Play,
  Download,
  Copy,
  CheckCircle2,
  Clock,
  FileText,
  MoreVertical,
  Loader2,
  TrendingUp,
  Maximize2,
  X,
} from "lucide-react";
import { Button } from "./button";
import { Badge } from "./badge";
import { GlowingCard } from "./glowing-card";
import { Progress } from "./progress";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "./dropdown-menu";


export interface Clip {
  id: string;
  startTime: number;
  endTime: number;
  duration: number;
  transcript: string;
  score?: number;
  description?: string;
  hashtags?: string[];
  thumbnailUrl?: string;
  previewUrl?: string;
  outputPath?: string;
  words?: Array<{
    text: string;
    start_time: number;
    end_time: number;
  }>;
}

interface ClipCardProps {
  clip: Clip;
  index: number;
  jobId: string;
  onPreview?: (clipId: string) => void;
  onLoadPreview?: (clipId: string) => Promise<string | null>;
}

export function ClipCard({ clip, index, jobId, onPreview, onLoadPreview }: ClipCardProps) {
  const [copied, setCopied] = useState(false);
  const [inlinePreviewUrl, setInlinePreviewUrl] = useState<string | null>(clip.previewUrl || null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState(0);
  const [exportMessage, setExportMessage] = useState("");
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const fullscreenVideoRef = useRef<HTMLVideoElement>(null);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const copyDescription = () => {
    if (clip.description) {
      navigator.clipboard.writeText(
        `${clip.description}\n\n${clip.hashtags?.map(h => `#${h}`).join(" ") || ""}`
      );
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleInlinePlay = async () => {
    if (inlinePreviewUrl) {
      if (videoRef.current) {
        if (isPlaying) {
          videoRef.current.pause();
          setIsPlaying(false);
        } else {
          videoRef.current.play();
          setIsPlaying(true);
        }
      }
      return;
    }

    // Load preview if not already loaded
    if (onLoadPreview) {
      setLoadingPreview(true);
      try {
        const url = await onLoadPreview(clip.id);
        if (url) {
          setInlinePreviewUrl(url);
          setTimeout(() => {
            if (videoRef.current) {
              videoRef.current.play();
              setIsPlaying(true);
            }
          }, 100);
        }
      } finally {
        setLoadingPreview(false);
      }
    } else if (onPreview) {
      onPreview(clip.id);
    }
  };

  const handleFullscreen = async (e: React.MouseEvent) => {
    e.stopPropagation();
    
    // Load preview first if needed
    if (!inlinePreviewUrl && onLoadPreview) {
      setLoadingPreview(true);
      try {
        const url = await onLoadPreview(clip.id);
        if (url) {
          setInlinePreviewUrl(url);
        }
      } finally {
        setLoadingPreview(false);
      }
    }
    
    setIsFullscreen(true);
    // Auto-play in fullscreen
    setTimeout(() => {
      if (fullscreenVideoRef.current) {
        fullscreenVideoRef.current.play();
      }
    }, 100);
  };

  const closeFullscreen = () => {
    setIsFullscreen(false);
    if (fullscreenVideoRef.current) {
      fullscreenVideoRef.current.pause();
    }
  };

  // Export with progress tracking
  const handleExport = async () => {
    if (exporting) return;

    setExporting(true);
    setExportProgress(0);
    setExportMessage("Starting export...");
    setDownloadUrl(null);

    try {
      const response = await fetch(`http://localhost:8000/api/clips/${jobId}/export/${clip.id}`, {
        method: "POST",
      });

      if (!response.ok) throw new Error("Failed to start export");

      const data = await response.json();

      const pollProgress = async () => {
        try {
          const statusRes = await fetch(`http://localhost:8000/api/clips/export/${data.export_id}/status`);
          if (!statusRes.ok) return;

          const status = await statusRes.json();
          setExportProgress(status.progress);
          setExportMessage(status.message);

          if (status.status === "completed") {
            setExporting(false);
            setDownloadUrl(status.download_url);
          } else if (status.status === "failed") {
            setExporting(false);
            setExportMessage("Export failed");
          } else {
            setTimeout(pollProgress, 500);
          }
        } catch (e) {
          console.error("Poll error:", e);
          setTimeout(pollProgress, 1000);
        }
      };

      pollProgress();

    } catch (error) {
      console.error("Export error:", error);
      setExporting(false);
      setExportMessage("Export failed");
    }
  };

  const handleDownload = () => {
    if (downloadUrl) {
      window.open(`http://localhost:8000${downloadUrl}`, "_blank");
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return "text-green-500";
    if (score >= 75) return "text-yellow-500";
    return "text-orange-500";
  };

  return (
    <>
      <GlowingCard
        className="overflow-hidden"
        glowColor={["purple", "blue", "cyan", "pink"][index % 4]}
      >
        <div className="p-3 space-y-2">
          {/* Compact Header */}
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0">
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary text-sm font-bold">
                {index + 1}
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-1.5">
                  <h3 className="font-medium text-sm">Clip {index + 1}</h3>
                  {clip.score && (
                    <Badge variant="outline" className={cn("text-[10px] px-1 py-0", getScoreColor(clip.score))}>
                      <TrendingUp className="h-2.5 w-2.5 mr-0.5" />
                      {Math.round(clip.score)}%
                    </Badge>
                  )}
                </div>
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  <span>{formatTime(clip.startTime)} - {formatTime(clip.endTime)}</span>
                  <Badge variant="secondary" className="text-[10px] px-1 py-0 ml-1">
                    {formatTime(clip.duration)}
                  </Badge>
                </div>
              </div>
            </div>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-7 w-7">
                  <MoreVertical className="h-3.5 w-3.5" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => onPreview?.(clip.id)}>
                  <Play className="h-4 w-4 mr-2" />
                  Open in Modal
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleExport}>
                  <Download className="h-4 w-4 mr-2" />
                  Export HQ
                </DropdownMenuItem>
                <DropdownMenuItem onClick={copyDescription}>
                  <Copy className="h-4 w-4 mr-2" />
                  Copy Description
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          {/* Compact Video Preview */}
          <div className="relative aspect-[9/12] rounded-md bg-muted overflow-hidden group">
            {inlinePreviewUrl ? (
              <video
                ref={videoRef}
                src={inlinePreviewUrl}
                className="h-full w-full object-cover"
                loop
                playsInline
                onEnded={() => setIsPlaying(false)}
                onPlay={() => setIsPlaying(true)}
                onPause={() => setIsPlaying(false)}
                onClick={() => {
                  if (videoRef.current) {
                    if (isPlaying) {
                      videoRef.current.pause();
                    } else {
                      videoRef.current.play();
                    }
                  }
                }}
              />
            ) : clip.thumbnailUrl ? (
              <img
                src={clip.thumbnailUrl}
                alt={`Clip ${index + 1}`}
                className="h-full w-full object-cover"
                onError={(e) => {
                  // Hide broken image
                  e.currentTarget.style.display = 'none';
                }}
              />
            ) : (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center text-muted-foreground">
                  <FileText className="h-6 w-6 mx-auto mb-1 opacity-50" />
                  <span className="text-xs">Click to Play</span>
                </div>
              </div>
            )}

            {/* Overlay controls for thumbnail */}
            {!inlinePreviewUrl && (
              <div
                className="absolute inset-0 flex items-center justify-center bg-black/40 transition-opacity cursor-pointer opacity-0 group-hover:opacity-100"
                onClick={handleInlinePlay}
              >
                {loadingPreview ? (
                  <Loader2 className="h-8 w-8 text-white animate-spin" />
                ) : (
                  <div className="rounded-full bg-white/20 backdrop-blur-sm p-3">
                    <Play className="h-6 w-6 text-white" fill="white" />
                  </div>
                )}
              </div>
            )}

            {/* Play/Pause overlay for video */}
            {inlinePreviewUrl && !isPlaying && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/30 cursor-pointer opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={() => videoRef.current?.play()}
              >
                <div className="rounded-full bg-white/20 backdrop-blur-sm p-4">
                  <Play className="h-8 w-8 text-white" fill="white" />
                </div>
              </div>
            )}

            {/* Fullscreen button */}
            <Button
              variant="ghost"
              size="icon"
              className="absolute top-1.5 right-1.5 h-7 w-7 bg-black/50 hover:bg-black/70 opacity-0 group-hover:opacity-100 transition-opacity z-30"
              onClick={handleFullscreen}
            >
              <Maximize2 className="h-3.5 w-3.5 text-white" />
            </Button>
          </div>

          {/* Compact Transcript */}
          <p className="text-xs text-muted-foreground line-clamp-2">
            {clip.transcript || "No transcript available"}
          </p>

          {/* Export Progress */}
          {exporting && (
            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">{exportMessage}</span>
                <span className="font-medium">{exportProgress}%</span>
              </div>
              <Progress value={exportProgress} className="h-1.5" />
            </div>
          )}

          {/* Download Ready */}
          {downloadUrl && !exporting && (
            <Button
              size="sm"
              className="w-full h-7 text-xs bg-green-600 hover:bg-green-700"
              onClick={handleDownload}
            >
              <Download className="h-3 w-3 mr-1" />
              Download Ready
            </Button>
          )}

          {/* Compact Actions - Only Export button now */}
          {!exporting && !downloadUrl && (
            <div className="flex gap-1.5">
              <Button
                size="sm"
                className="flex-1 h-7 text-xs"
                onClick={handleExport}
              >
                <Download className="h-3 w-3 mr-1" />
                Export
              </Button>
              <Button
                variant="outline"
                size="icon"
                className="h-7 w-7"
                onClick={copyDescription}
              >
                {copied ? (
                  <CheckCircle2 className="h-3 w-3 text-green-500" />
                ) : (
                  <Copy className="h-3 w-3" />
                )}
              </Button>
            </div>
          )}
        </div>
      </GlowingCard>

      {/* Fullscreen Modal */}
      <AnimatePresence>
        {isFullscreen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm"
            onClick={closeFullscreen}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="relative h-[90vh] aspect-[9/16] max-w-[90vw]"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Close button */}
              <Button
                variant="ghost"
                size="icon"
                className="absolute -top-12 right-0 h-10 w-10 text-white hover:bg-white/20 z-30"
                onClick={closeFullscreen}
              >
                <X className="h-6 w-6" />
              </Button>

              {/* Video with transcription */}
              <div className="h-full w-full rounded-lg overflow-hidden bg-black">
                {inlinePreviewUrl ? (
                  <video
                    ref={fullscreenVideoRef}
                    src={inlinePreviewUrl}
                    className="h-full w-full object-contain"
                    controls
                    autoPlay
                    loop
                    playsInline
                  />
                ) : (
                  <div className="h-full w-full flex items-center justify-center">
                    <Loader2 className="h-12 w-12 text-white animate-spin" />
                  </div>
                )}
              </div>

              {/* Info bar */}
              <div className="absolute top-0 left-0 right-0 p-4 bg-gradient-to-b from-black/80 to-transparent z-20">
                <div className="flex items-center justify-between text-white">
                  <div>
                    <h3 className="font-semibold">Clip {index + 1}</h3>
                    <p className="text-sm text-white/70">
                      {formatTime(clip.startTime)} - {formatTime(clip.endTime)} ({formatTime(clip.duration)})
                    </p>
                  </div>
                  {clip.score && (
                    <Badge className={cn("text-sm", getScoreColor(clip.score))}>
                      <TrendingUp className="h-4 w-4 mr-1" />
                      {Math.round(clip.score)}% viral
                    </Badge>
                  )}
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

interface ClipsGridProps {
  clips: Clip[];
  jobId: string;
  onPreview?: (clipId: string) => void;
  onLoadPreview?: (clipId: string) => Promise<string | null>;
}

export function ClipsGrid({ clips, jobId, onPreview, onLoadPreview }: ClipsGridProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
      {clips.map((clip, index) => (
        <motion.div
          key={clip.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.05 }}
        >
          <ClipCard
            clip={clip}
            index={index}
            jobId={jobId}
            onPreview={onPreview}
            onLoadPreview={onLoadPreview}
          />
        </motion.div>
      ))}
    </div>
  );
}
