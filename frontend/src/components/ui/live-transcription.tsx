"use client";

import { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import {
  FileText,
  Mic,
  Loader2,
  Sparkles,
  Globe,
  CheckCircle2,
} from "lucide-react";
import { Badge } from "./badge";
import { Progress } from "./progress";

interface LiveTranscriptionProps {
  jobId: string | null;
  onComplete?: (transcript: string) => void;
}

interface TranscriptSegment {
  text: string;
  word_count: number;
}

export function LiveTranscription({ jobId, onComplete }: LiveTranscriptionProps) {
  const [isConnected, setIsConnected] = useState(false);
  const [stage, setStage] = useState<string>("waiting");
  const [progress, setProgress] = useState(0);
  const [transcript, setTranscript] = useState("");
  const [wordCount, setWordCount] = useState(0);
  const [summary, setSummary] = useState<any>(null);
  const [detectedLanguage, setDetectedLanguage] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!jobId) return;

    // Connect to SSE stream for upload job progress
    const eventSource = new EventSource(`http://localhost:8000/api/upload/stream/${jobId}`);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setIsConnected(true);
      console.log("SSE connection opened");
    };

    eventSource.onmessage = (event: MessageEvent) => {
      console.log("SSE message:", event.data);
    };

    eventSource.addEventListener("progress", (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        setStage(data.stage || "processing");
        setProgress(data.percent || 0);
        if (data.transcript) {
          setTranscript(data.transcript);
        }
        if (data.word_count) {
          setWordCount(data.word_count);
        }
      } catch (e) {
        console.error("Error parsing progress event:", e);
      }
    });

    eventSource.addEventListener("complete", (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        setStage("complete");
        setProgress(100);
        if (data.transcript) {
          setTranscript(data.transcript);
        }
        if (data.summary) {
          setSummary(data.summary);
        }
        onComplete?.(data.transcript || transcript);
        eventSource.close();
        setIsConnected(false);
      } catch (e) {
        console.error("Error parsing complete event:", e);
      }
    });

    eventSource.onerror = (error: Event) => {
      console.error("SSE error:", error);
      setIsConnected(false);
      // Don't close on error, let it retry
    };

    return () => {
      eventSource.close();
      setIsConnected(false);
    };
  }, [jobId, onComplete, transcript]);

  // Auto-scroll to bottom of transcript
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [transcript]);

  if (!jobId) return null;

  const getStageIcon = () => {
    switch (stage) {
      case "download":
        return <Globe className="h-5 w-5" />;
      case "transcribe":
        return <Mic className="h-5 w-5" />;
      case "summarize":
        return <Sparkles className="h-5 w-5" />;
      case "complete":
        return <CheckCircle2 className="h-5 w-5" />;
      default:
        return <Loader2 className="h-5 w-5 animate-spin" />;
    }
  };

  const getStageLabel = () => {
    switch (stage) {
      case "download":
        return "Downloading video...";
      case "transcribe":
        return "Transcribing audio...";
      case "summarize":
        return "Generating AI summary...";
      case "translate":
        return "Translating...";
      case "complete":
        return "Processing complete!";
      default:
        return "Initializing...";
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl border border-border bg-card overflow-hidden"
    >
      {/* Header */}
      <div className="p-4 border-b border-border bg-muted/30">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={cn(
              "rounded-lg p-2",
              stage === "complete" ? "bg-green-500/20" : "bg-primary/20"
            )}>
              <FileText className={cn(
                "h-5 w-5",
                stage === "complete" ? "text-green-500" : "text-primary"
              )} />
            </div>
            <div>
              <h3 className="font-semibold flex items-center gap-2">
                Live Transcription
                {isConnected && (
                  <span className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                    <span className="text-xs font-normal text-muted-foreground">Live</span>
                  </span>
                )}
              </h3>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                {getStageIcon()}
                <span>{getStageLabel()}</span>
                {wordCount > 0 && (
                  <span className="text-xs">• {wordCount} words</span>
                )}
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {detectedLanguage && (
              <Badge variant="outline" className="text-xs">
                {detectedLanguage.toUpperCase()}
              </Badge>
            )}
            <Badge variant={stage === "complete" ? "default" : "secondary"}>
              {Math.round(progress)}%
            </Badge>
          </div>
        </div>
        
        {/* Progress Bar */}
        <Progress value={progress} className="h-1 mt-3" />
      </div>

      {/* Transcript Display */}
      <div 
        ref={scrollRef}
        className="p-4 max-h-80 overflow-y-auto space-y-4"
      >
        {transcript ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="prose prose-sm dark:prose-invert max-w-none"
          >
            {/* Show latest part of transcript prominently */}
            <div className="text-lg leading-relaxed">
              {transcript}
            </div>
          </motion.div>
        ) : (
          <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
            <Loader2 className="h-8 w-8 animate-spin mb-2" />
            <p className="text-sm">Waiting for transcription to start...</p>
          </div>
        )}

        {/* Word count indicator */}
        {wordCount > 0 && (
          <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t border-border">
            <span>{wordCount} words transcribed</span>
            <span>{Math.round(wordCount * 0.15)} words/min estimated</span>
          </div>
        )}
      </div>

      {/* Summary Section (appears when complete) */}
      <AnimatePresence>
        {summary && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-border bg-muted/20"
          >
            <div className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="h-4 w-4 text-cyan-500" />
                <h4 className="font-semibold text-sm">AI Summary</h4>
              </div>
              
              <p className="text-sm text-muted-foreground mb-3">
                {summary.summary}
              </p>
              
              {summary.key_points && summary.key_points.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-medium text-muted-foreground">Key Points:</p>
                  <ul className="space-y-1">
                    {summary.key_points.slice(0, 3).map((point: string, i: number) => (
                      <li key={i} className="text-sm flex items-start gap-2">
                        <span className="text-primary">•</span>
                        {point}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
