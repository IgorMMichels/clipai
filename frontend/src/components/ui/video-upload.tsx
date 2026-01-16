"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import {
  Upload,
  FileVideo,
  X,
  CheckCircle2,
  Loader2,
  AlertCircle,
  Youtube,
  Link as LinkIcon,
  FileText,
} from "lucide-react";
import { Button } from "./button";
import { Progress } from "./progress";
import { Badge } from "./badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./tabs";
import { LiveTranscription } from "./live-transcription";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface UploadedFile {
  file: File | { name: string; size: number };
  id: string;
  progress: number;
  status: "uploading" | "processing" | "completed" | "error";
  message?: string;
  jobId?: string;
}

interface VideoUploadProps {
  onUploadComplete?: (jobId: string) => void;
  settings?: {
    language: string;
    aspectRatio: string;
    generateDescription: boolean;
    descriptionLanguage: string;
  };
}

export function VideoUpload({ onUploadComplete, settings }: VideoUploadProps) {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [showLiveTranscription, setShowLiveTranscription] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map((file) => ({
      file,
      id: Math.random().toString(36).substr(2, 9),
      progress: 0,
      status: "uploading" as const,
    }));
    setFiles((prev) => [...prev, ...newFiles]);
    
    // Start upload for each file
    newFiles.forEach((fileData) => {
      uploadFile(fileData);
    });
  }, [settings]); // Re-create if settings change

  const getAspectRatio = (ratioStr: string = "9:16") => {
    const [w, h] = ratioStr.split(":").map(Number);
    return { w: w || 9, h: h || 16 };
  };

  const uploadFile = async (fileData: UploadedFile) => {
    if (!("name" in fileData.file)) return; // Type guard
    
    setIsUploading(true);
    
    try {
      const formData = new FormData();
      formData.append("file", fileData.file as File);
      formData.append("language", settings?.language === "auto" ? "" : settings?.language || "");
      
      const { w, h } = getAspectRatio(settings?.aspectRatio);
      formData.append("aspect_ratio_w", w.toString());
      formData.append("aspect_ratio_h", h.toString());
      
      formData.append("generate_description", String(settings?.generateDescription ?? true));
      formData.append("description_language", settings?.descriptionLanguage || "en");

      // Simulate progress (in real app, use XMLHttpRequest for progress)
      const progressInterval = setInterval(() => {
        setFiles((prev) =>
          prev.map((f) =>
            f.id === fileData.id && f.progress < 90
              ? { ...f, progress: f.progress + 10 }
              : f
          )
        );
      }, 200);

      const response = await fetch(`${API_URL}/api/upload/`, {
        method: "POST",
        body: formData,
      });

      clearInterval(progressInterval);

      if (!response.ok) {
        throw new Error("Upload failed");
      }

      const data = await response.json();

      setFiles((prev) =>
        prev.map((f) =>
          f.id === fileData.id
            ? {
                ...f,
                progress: 100,
                status: "processing",
                message: "Processing video...",
                jobId: data.id,
              }
            : f
        )
      );

      // Show live transcription
      setActiveJobId(data.id);
      setShowLiveTranscription(true);

      // Poll for status
      pollJobStatus(fileData.id, data.id);
    } catch (error) {
      setFiles((prev) =>
        prev.map((f) =>
          f.id === fileData.id
            ? { ...f, status: "error", message: "Upload failed. Is the backend running?" }
            : f
        )
      );
    }
    
    setIsUploading(false);
  };

  const handleYoutubeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!youtubeUrl) return;

    const id = Math.random().toString(36).substr(2, 9);
    const fileData: UploadedFile = {
      file: { name: youtubeUrl, size: 0 },
      id,
      progress: 0,
      status: "uploading",
      message: "Initializing YouTube download...",
    };

    setFiles((prev) => [...prev, fileData]);
    setYoutubeUrl(""); // Clear input
    setIsUploading(true);

    try {
      const { w, h } = getAspectRatio(settings?.aspectRatio);
      
      const response = await fetch(`${API_URL}/api/upload/youtube`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: fileData.file.name,
          language: settings?.language === "auto" ? null : settings?.language,
          aspect_ratio: [w, h],
          generate_description: settings?.generateDescription ?? true,
          description_language: settings?.descriptionLanguage || "en"
        })
      });

      if (!response.ok) throw new Error("YouTube submission failed");
      
      const data = await response.json();
      
      setFiles((prev) =>
        prev.map((f) =>
          f.id === id
            ? {
                ...f,
                progress: 5,
                status: "processing",
                message: "Queued for download...",
                jobId: data.id,
              }
            : f
        )
      );
      
      // Show live transcription
      setActiveJobId(data.id);
      setShowLiveTranscription(true);
      
      pollJobStatus(id, data.id);

    } catch (error) {
      setFiles((prev) =>
        prev.map((f) =>
          f.id === id
            ? { ...f, status: "error", message: "Failed to submit YouTube video" }
            : f
        )
      );
    }
    setIsUploading(false);
  };

  const pollJobStatus = async (fileId: string, jobId: string) => {
    const poll = async () => {
      try {
        const response = await fetch(`${API_URL}/api/upload/status/${jobId}`);
        const data = await response.json();

        setFiles((prev) =>
          prev.map((f) =>
            f.id === fileId
              ? {
                  ...f,
                  progress: data.progress,
                  message: data.message,
                  status: data.status === "completed" ? "completed" : 
                          data.status === "failed" ? "error" : "processing",
                }
              : f
          )
        );

        if (data.status === "completed") {
          setShowLiveTranscription(false);
          onUploadComplete?.(jobId);
        } else if (data.status === "failed") {
          setShowLiveTranscription(false);
        } else if (data.status !== "failed") {
          setTimeout(poll, 2000);
        }
      } catch {
        setTimeout(poll, 2000);
      }
    };

    poll();
  };

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "video/*": [".mp4", ".mov", ".avi", ".mkv", ".webm"],
    },
    maxSize: 500 * 1024 * 1024, // 500MB
  });

  return (
    <div className="space-y-6">
      <Tabs defaultValue="upload" className="w-full">
        <TabsList className="grid w-full grid-cols-2 mb-4">
          <TabsTrigger value="upload" className="flex items-center gap-2">
            <Upload className="h-4 w-4" />
            File Upload
          </TabsTrigger>
          <TabsTrigger value="youtube" className="flex items-center gap-2">
            <Youtube className="h-4 w-4" />
            YouTube URL
          </TabsTrigger>
        </TabsList>

        <TabsContent value="upload">
          {/* Dropzone - wrapper div handles dropzone, inner div handles styling */}
          <div {...getRootProps()}>
            <div
              className={cn(
                "relative rounded-2xl border-2 border-dashed p-12 text-center cursor-pointer transition-all duration-300 hover:scale-[1.01] active:scale-[0.99]",
                isDragActive
                  ? "border-primary bg-primary/5 glow-purple"
                  : "border-border hover:border-primary/50 hover:bg-accent/50"
              )}
            >
              <input {...getInputProps()} />
              
              <div className="flex flex-col items-center gap-4">
                <motion.div
                  className={cn(
                    "rounded-full p-4 transition-colors",
                    isDragActive ? "bg-primary/20" : "bg-muted"
                  )}
                  animate={{ y: isDragActive ? -5 : 0 }}
                >
                  <Upload className={cn(
                    "h-8 w-8 transition-colors",
                    isDragActive ? "text-primary" : "text-muted-foreground"
                  )} />
                </motion.div>
                
                <div>
                  <p className="text-lg font-medium">
                    {isDragActive ? "Drop your video here" : "Drag & drop your video"}
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    or click to browse. Supports MP4, MOV, AVI, MKV, WebM (max 500MB)
                  </p>
                </div>
                
                <Button variant="outline" className="mt-2">
                  Browse Files
                </Button>
              </div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="youtube">
          <div className="rounded-2xl border border-border p-8 bg-card">
             <form onSubmit={handleYoutubeSubmit} className="flex flex-col gap-4">
               <div className="flex flex-col gap-2">
                 <label htmlFor="youtube-url" className="text-sm font-medium">
                   YouTube Video URL
                 </label>
                 <div className="flex gap-2">
                   <div className="relative flex-1">
                     <LinkIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                     <input
                       id="youtube-url"
                       type="url"
                       placeholder="https://www.youtube.com/watch?v=..."
                       className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 pl-9 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                       value={youtubeUrl}
                       onChange={(e) => setYoutubeUrl(e.target.value)}
                       required
                     />
                   </div>
                   <Button type="submit" disabled={!youtubeUrl || isUploading}>
                     {isUploading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Process"}
                   </Button>
                 </div>
                 <p className="text-xs text-muted-foreground">
                   Supports standard YouTube videos and Shorts.
                 </p>
               </div>
             </form>
          </div>
        </TabsContent>
      </Tabs>

      {/* File list */}
      <AnimatePresence>
        {files.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-3"
          >
            {files.map((fileData) => (
              <motion.div
                key={fileData.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="flex items-center gap-4 p-4 rounded-xl border border-border bg-card"
              >
                <div className="flex-shrink-0">
                  <div className="rounded-lg bg-muted p-3">
                    {fileData.file.name.includes("youtube") || fileData.file.name.includes("http") ? (
                         <Youtube className="h-6 w-6 text-red-500" />
                    ) : (
                        <FileVideo className="h-6 w-6 text-muted-foreground" />
                    )}
                  </div>
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="font-medium truncate">{fileData.file.name}</p>
                    <Badge variant={
                      fileData.status === "completed" ? "default" :
                      fileData.status === "error" ? "destructive" :
                      "secondary"
                    }>
                      {fileData.status}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">
                     {fileData.message}
                  </p>
                  {(fileData.status === "uploading" || fileData.status === "processing") && (
                    <Progress value={fileData.progress} className="h-1 mt-2" />
                  )}
                </div>

                <div className="flex-shrink-0">
                  {fileData.status === "completed" && (
                    <CheckCircle2 className="h-6 w-6 text-green-500" />
                  )}
                  {fileData.status === "error" && (
                    <AlertCircle className="h-6 w-6 text-destructive" />
                  )}
                  {(fileData.status === "uploading" || fileData.status === "processing") && (
                    <Loader2 className="h-6 w-6 animate-spin text-primary" />
                  )}
                </div>

                <Button
                  variant="ghost"
                  size="icon"
                  className="flex-shrink-0"
                  onClick={() => removeFile(fileData.id)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Live Transcription Panel */}
      <AnimatePresence>
        {showLiveTranscription && activeJobId && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="mt-6"
          >
            <LiveTranscription 
              jobId={activeJobId}
              onComplete={(transcript) => {
                console.log("Transcription complete:", transcript);
              }}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
