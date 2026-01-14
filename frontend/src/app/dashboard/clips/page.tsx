"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { ClipsGrid, Clip } from "@/components/ui/clip-card";
import { GlowingCard } from "@/components/ui/glowing-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Download,
  FileVideo,
  Loader2,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import Link from "next/link";

interface JobData {
  id: string;
  filename: string;
  status: string;
  progress: number;
  message: string;
  language?: string;
  transcript?: string;
  facecam_region?: {
    x: number;
    y: number;
    width: number;
    height: number;
    is_corner: string;
    confidence: number;
  };
  clips: Array<{
    id: string;
    start_time: number;
    end_time: number;
    duration: number;
    transcript: string;
    score?: number;
    description?: string;
    hashtags?: string[];
    words?: Array<{
      text: string;
      start_time: number;
      end_time: number;
    }>;
  }>;
}

import { PreviewModal } from "@/components/preview-modal";

export default function ClipsPage() {
  const searchParams = useSearchParams();
  const jobId = searchParams.get("job");
  
  const [job, setJob] = useState<JobData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [useStackedLayout, setUseStackedLayout] = useState(false);
  
  // Preview state
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [activeClipId, setActiveClipId] = useState<string | null>(null);

  useEffect(() => {
    if (jobId) {
      fetchJobData(jobId);
    }
  }, [jobId]);

  const fetchJobData = async (id: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`http://localhost:8000/api/upload/job/${id}`);
      if (!response.ok) throw new Error("Failed to fetch job");
      const data = await response.json();
      setJob(data);
      
      // Poll if still processing
      if (data.status !== "completed" && data.status !== "failed") {
        setTimeout(() => fetchJobData(id), 2000);
      }
    } catch (err) {
      setError("Failed to load job data. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  const handlePreview = async (clipId: string) => {
    if (!job) return;
    try {
        // Request preview generation with PiP but NO subtitles
        const response = await fetch(`http://localhost:8000/api/clips/${job.id}/preview/${clipId}?with_subtitles=false&with_pip=${job.facecam_region ? 'true' : 'false'}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
        });

        if (!response.ok) throw new Error("Preview generation failed");

        const data = await response.json();
        if (data.url) {
            setPreviewUrl(`http://localhost:8000${data.url}`);
            setActiveClipId(clipId);
            setPreviewOpen(true);
        }
    } catch (err) {
        console.error("Preview error:", err);
        setError("Failed to generate preview");
    }
  };

  const handleLoadPreview = async (clipId: string): Promise<string | null> => {
    if (!job) return null;
    try {
        const response = await fetch(`http://localhost:8000/api/clips/${job.id}/preview/${clipId}?with_subtitles=false&with_pip=${job.facecam_region ? 'true' : 'false'}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
        });

        if (!response.ok) return null;

        const data = await response.json();
        if (data.url) {
            return `http://localhost:8000${data.url}`;
        }
        return null;
    } catch (err) {
        console.error("Preview error:", err);
        return null;
    }
  };

  const clips: Clip[] = job?.clips.map(c => ({
    id: c.id,
    startTime: c.start_time,
    endTime: c.end_time,
    duration: c.duration,
    transcript: c.transcript,
    score: c.score,
    description: c.description,
    hashtags: c.hashtags,
    thumbnailUrl: `http://localhost:8000/api/clips/${job.id}/thumbnail/${c.id}`,
    words: c.words,
  })) || [];

  // No job selected - show empty state
  if (!jobId) {
    return (
      <div className="p-6 lg:p-8">
        <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
          <div className="rounded-full bg-muted p-6 mb-6">
            <FileVideo className="h-12 w-12 text-muted-foreground" />
          </div>
          <h2 className="text-2xl font-bold mb-2">No Clips Yet</h2>
          <p className="text-muted-foreground mb-6 max-w-md">
            Upload a video to start generating clips automatically. Our AI will find the best moments for you.
          </p>
          <Link href="/dashboard/upload">
            <Button size="lg" className="glow-purple">
              Upload Video
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  // Loading state
  if (loading && !job) {
    return (
      <div className="p-6 lg:p-8 flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading job data...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="p-6 lg:p-8 flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
          <p className="text-muted-foreground mb-4">{error}</p>
          <Button onClick={() => fetchJobData(jobId)}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold tracking-tight">My Clips</h1>
            <Badge variant={
              job?.status === "completed" ? "default" :
              job?.status === "failed" ? "destructive" :
              "secondary"
            }>
              {job?.status || "unknown"}
            </Badge>
          </div>
          {job && (
            <p className="text-muted-foreground mt-1">
              {job.filename} • {clips.length} clips found
            </p>
          )}
        </div>
        
        <div className="flex items-center gap-3">
            <Button 
                variant={useStackedLayout ? "default" : "outline"}
                onClick={() => setUseStackedLayout(!useStackedLayout)}
                className={useStackedLayout ? "bg-purple-600 hover:bg-purple-700" : ""}
            >
                {useStackedLayout ? "Stacked Layout (Facecam)" : "Default Layout"}
            </Button>

            {clips.length > 0 && (
              <Button className="glow-purple">
                <Download className="h-4 w-4 mr-2" />
                Export All
              </Button>
            )}
        </div>
      </div>

      {/* Processing status */}
      {job && job.status !== "completed" && job.status !== "failed" && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <GlowingCard className="p-6" glowColor="blue">
            <div className="flex items-center gap-4">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <div className="flex-1">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium">{job.message}</span>
                  <span className="text-sm text-muted-foreground">{job.progress}%</span>
                </div>
                <Progress value={job.progress} />
              </div>
            </div>
          </GlowingCard>
        </motion.div>
      )}

      {/* Completed status */}
      {job?.status === "completed" && clips.length === 0 && (
        <GlowingCard className="p-6" glowColor="cyan">
          <div className="flex items-center gap-4">
            <CheckCircle2 className="h-8 w-8 text-green-500" />
            <div>
              <p className="font-medium">Processing Complete</p>
              <p className="text-sm text-muted-foreground">
                No clips found matching the criteria. Try with a different video.
              </p>
            </div>
          </div>
        </GlowingCard>
      )}

      {/* Facecam detection status */}
      {job?.facecam_region && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <GlowingCard className="p-4" glowColor="cyan">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="h-5 w-5 text-cyan-500" />
              <div>
                <span className="font-medium">Facecam Detected</span>
                <span className="text-sm text-muted-foreground ml-2">
                  Position: {job.facecam_region.is_corner} ({Math.round(job.facecam_region.confidence * 100)}% confidence)
                </span>
              </div>
            </div>
          </GlowingCard>
        </motion.div>
      )}

      {/* Clips grid */}
      {clips.length > 0 && jobId && (
        <ClipsGrid
          clips={clips}
          jobId={jobId}
          onPreview={handlePreview}
          onLoadPreview={handleLoadPreview}
        />
      )}

      {/* Transcript section */}
      {job?.transcript && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <GlowingCard className="p-6" glowColor="purple">
            <h3 className="font-semibold mb-4">Full Transcript</h3>
            <div className="max-h-64 overflow-y-auto">
              <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                {job.transcript}
              </p>
            </div>
          </GlowingCard>
        </motion.div>
      )}
      
      <PreviewModal
        isOpen={previewOpen}
        onClose={() => setPreviewOpen(false)}
        url={previewUrl}
        title={activeClipId ? `Clip ${clips.findIndex(c => c.id === activeClipId) + 1}` : undefined}
      />
    </div>
  );
}
