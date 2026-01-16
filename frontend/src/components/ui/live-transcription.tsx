"use client";

import { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import {
  FileText,
  Mic,
  Loader2,
  Sparkles,
  CheckCircle2,
  Play,
  Volume2,
  Languages,
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
  const transcriptContainerRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!jobId) return;

    const eventSource = new EventSource(`${API_URL}/api/upload/stream/${jobId}`);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setIsConnected(true);
      console.log("SSE connection opened");
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
        if (data.transcript_language) {
          setDetectedLanguage(data.transcript_language);
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
    };

    return () => {
      eventSource.close();
      setIsConnected(false);
    };
  }, [jobId, onComplete]);

  useEffect(() => {
    if (transcriptContainerRef.current) {
      transcriptContainerRef.current.scrollTop = transcriptContainerRef.current.scrollHeight;
    }
  }, [transcript]);

  if (!jobId) return null;

  const getStageIcon = () => {
    switch (stage) {
      case "download":
        return <Play className="h-5 w-5" />;
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
        return "Baixando vídeo...";
      case "transcribe":
        return "Transcrevendo áudio...";
      case "summarize":
        return "Gerando resumo...";
      case "translate":
        return "Traduzindo...";
      case "complete":
        return "Concluído!";
      default:
        return "Inicializando...";
    }
  };

  return (
    <div className="space-y-6">
      {/* Main Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl border-2 border-cyan-500/30 bg-gradient-to-br from-slate-50 dark:from-slate-900/50 to-slate-100 dark:to-slate-900 overflow-hidden shadow-2xl"
      >
        {/* Header */}
        <div className="p-5 border-b border-white/10 dark:border-white/5 bg-white/50 dark:bg-white/5 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={cn(
                "rounded-xl p-3",
                stage === "complete" ? "bg-green-500" : "bg-primary"
              )}>
                <FileText className={cn(
                  "h-6 w-6 text-white",
                  stage === "complete" ? "text-green-500" : "text-primary"
                )} />
              </div>
              <div>
                <h3 className="text-xl font-bold text-foreground flex items-center gap-2">
                  Transcrição ao Vivo
                  {isConnected && (
                    <span className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                      <span className="text-sm font-normal text-muted-foreground">Ao Vivo</span>
                    </span>
                  )}
                </h3>
                <div className="flex items-center gap-3 text-sm text-muted-foreground">
                  {getStageIcon()}
                  <span className="font-medium">{getStageLabel()}</span>
                  {wordCount > 0 && (
                    <Badge variant="outline" className="ml-2">
                      {wordCount} palavras
                    </Badge>
                  )}
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              {detectedLanguage && (
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/80 dark:bg-slate-800">
                  <Languages className="h-4 w-4 text-primary" />
                  <span className="text-xs font-semibold uppercase">{detectedLanguage}</span>
                </div>
              )}
              <Badge variant={stage === "complete" ? "default" : "secondary"} className="text-sm px-4 py-1.5">
                {Math.round(progress)}%
              </Badge>
            </div>
          </div>
          
          {/* Progress Bar */}
          <div className="px-5 pb-3">
            <Progress value={progress} className="h-1.5" />
          </div>
        </div>

        {/* Live Transcription Display */}
        <div 
          ref={transcriptContainerRef}
          className="h-[500px] overflow-y-auto bg-gradient-to-b from-slate-50 dark:from-slate-900/50 to-transparent p-8 space-y-5"
        >
          {transcript ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-4"
            >
              {/* Live word cloud */}
              <div className="prose prose-lg dark:prose-invert max-w-none">
                <p className="text-3xl leading-relaxed font-medium tracking-wide text-foreground bg-white/90 dark:bg-slate-800/90 p-6 rounded-2xl shadow-lg">
                  {transcript}
                </p>
              </div>
            </motion.div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
              <Loader2 className="h-16 w-16 animate-spin mb-6 text-primary" />
              <p className="text-base">Aguardando transcrição...</p>
              <p className="text-sm text-muted-foreground mt-2">O áudio será processado e as palavras aparecerão aqui em tempo real</p>
            </div>
          )}

          {/* Stats bar at bottom */}
          {wordCount > 0 && (
            <div className="absolute bottom-0 left-0 right-0 px-6 py-4 border-t border-white/10 dark:border-white/5 bg-white/90 dark:bg-slate-900/90 backdrop-blur-sm flex items-center justify-between text-sm">
              <div className="flex items-center gap-4 text-muted-foreground">
                <div className="flex items-center gap-3">
                  <Volume2 className="h-5 w-5" />
                  <div>
                    <span className="text-lg font-semibold">{wordCount}</span>
                    <span className="text-sm text-muted-foreground ml-1">palavras transcritas</span>
                  </div>
                </div>
                {wordCount > 0 && (
                  <Badge variant="outline" className="ml-3 text-xs">
                    ~{Math.round(wordCount * 0.15)} palavras/min
                  </Badge>
                )}
              </div>
              {isConnected && (
                <div className="flex items-center gap-3 text-green-600 dark:text-green-400">
                  <div className="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse" />
                  <span className="text-sm font-bold uppercase tracking-wide">Transmitindo</span>
                </div>
              )}
            </div>
          )}
        </div>
      </motion.div>

      {/* Summary Section */}
      <AnimatePresence>
        {summary && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="rounded-2xl border-2 border-cyan-500/30 bg-gradient-to-br from-cyan-50 dark:from-cyan-950/10 to-cyan-100 dark:to-cyan-900/50 overflow-hidden shadow-2xl mt-6"
          >
            <div className="p-6">
              <div className="flex items-center gap-3 mb-4 border-b border-cyan-500/20 dark:border-cyan-400/20 pb-4">
                <Sparkles className="h-6 w-6 text-cyan-600 dark:text-cyan-400" />
                <h4 className="text-2xl font-bold text-foreground">Resumo com IA</h4>
              </div>
              
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-4"
              >
                {summary.summary && (
                  <div>
                    <p className="text-xl leading-relaxed text-foreground">
                      {summary.summary}
                    </p>
                  </div>
                )}
                
                {summary.key_points && summary.key_points.length > 0 && (
                  <div className="mt-4 space-y-3">
                    <p className="text-base font-semibold text-muted-foreground uppercase tracking-wider">Pontos Chave</p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {summary.key_points.slice(0, 6).map((point: string, i: number) => (
                        <motion.div
                          key={i}
                          initial={{ opacity: 0, scale: 0.95 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ delay: i * 0.05 }}
                          className="rounded-2xl p-5 bg-white/50 dark:bg-slate-800/50 border border-white/10 dark:border-white/5 hover:border-cyan-500/30 dark:hover:border-cyan-400/30 transition-all duration-300"
                        >
                          <div className="flex items-start gap-3">
                            <div className="flex-shrink-0 mt-1">
                              <div className="w-2 h-2 rounded-full bg-cyan-500 dark:bg-cyan-400" />
                            </div>
                            <p className="text-base leading-relaxed text-foreground">
                              {point}
                            </p>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                )}

                {summary.topics && summary.topics.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-white/10 dark:border-white/5">
                    <p className="text-base font-semibold text-muted-foreground">Tópicos</p>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {summary.topics.map((topic: string, i: number) => (
                        <Badge key={i} variant="secondary" className="text-sm px-4 py-2">
                          {topic}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </motion.div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
