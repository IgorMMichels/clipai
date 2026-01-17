"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { GlowingCard } from "@/components/ui/glowing-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Trash2,
  HardDrive,
  Upload,
  FileVideo,
  FolderOpen,
  RefreshCw,
  AlertTriangle,
  Loader2,
} from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FileInfo {
  name: string;
  path: string;
  size_mb: number;
  is_dir: boolean;
  created: string;
  modified: string;
  file_count?: number;
}

interface StorageSummary {
  uploads: { count: number; size_mb: number; path: string };
  outputs: { count: number; size_mb: number; path: string };
  total_size_mb: number;
}

export default function StoragePage() {
  const [summary, setSummary] = useState<StorageSummary | null>(null);
  const [uploads, setUploads] = useState<FileInfo[]>([]);
  const [outputs, setOutputs] = useState<FileInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch storage summary
      const summaryRes = await fetch(`${API_URL}/api/storage/summary`);
      if (summaryRes.ok) {
        const summaryData = await summaryRes.json();
        setSummary(summaryData);
      }

      // Fetch uploads list
      const uploadsRes = await fetch(`${API_URL}/api/storage/uploads`);
      if (uploadsRes.ok) {
        const uploadsData = await uploadsRes.json();
        setUploads(uploadsData.files || []);
      }

      // Fetch outputs list
      const outputsRes = await fetch(`${API_URL}/api/storage/outputs`);
      if (outputsRes.ok) {
        const outputsData = await outputsRes.json();
        setOutputs(outputsData.folders || []);
      }
    } catch (err) {
      console.error("Error fetching data:", err);
    } finally {
      setLoading(false);
    }
  };

  const deleteUpload = async (filename: string) => {
    if (!confirm(`Delete ${filename}?`)) return;

    setDeleting(filename);
    try {
      const res = await fetch(`${API_URL}/api/storage/uploads/${filename}`, {
        method: "DELETE",
      });
      if (res.ok) {
        fetchData();
      }
    } catch (err) {
      console.error("Error deleting:", err);
    } finally {
      setDeleting(null);
    }
  };

  const deleteOutput = async (foldername: string) => {
    if (!confirm(`Delete ${foldername} and all its clips?`)) return;

    setDeleting(foldername);
    try {
      const res = await fetch(`${API_URL}/api/storage/outputs/${foldername}`, {
        method: "DELETE",
      });
      if (res.ok) {
        fetchData();
      }
    } catch (err) {
      console.error("Error deleting:", err);
    } finally {
      setDeleting(null);
    }
  };

  const clearAll = async (type: "uploads" | "outputs" | "all") => {
    const messages = {
      uploads: "Delete ALL uploaded videos?",
      outputs: "Delete ALL generated clips?",
      all: "Delete ALL files (uploads + outputs)?",
    };
    
    if (!confirm(messages[type])) return;

    setDeleting(type);
    try {
      const res = await fetch(`${API_URL}/api/storage/clear/${type}`, {
        method: "DELETE",
      });
      if (res.ok) {
        const data = await res.json();
        alert(`Freed ${data.total_freed_mb || data.freed_mb} MB`);
        fetchData();
      }
    } catch (err) {
      console.error("Error clearing:", err);
    } finally {
      setDeleting(null);
    }
  };

  const formatSize = (mb: number) => {
    if (mb >= 1024) return `${(mb / 1024).toFixed(2)} GB`;
    return `${mb.toFixed(2)} MB`;
  };

  const formatDate = (isoString: string) => {
    return new Date(isoString).toLocaleString();
  };

  if (loading) {
    return (
      <div className="p-6 lg:p-8 flex items-center justify-center min-h-[60vh]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Storage Manager</h1>
          <p className="text-muted-foreground mt-1">
            Manage your uploaded videos and generated clips
          </p>
        </div>
        <Button variant="outline" onClick={fetchData}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <GlowingCard className="p-6" glowColor="blue">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-full bg-blue-500/10">
                <Upload className="h-6 w-6 text-blue-500" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Uploads</p>
                <p className="text-2xl font-bold">{formatSize(summary.uploads.size_mb)}</p>
                <p className="text-xs text-muted-foreground">{summary.uploads.count} files</p>
              </div>
            </div>
          </GlowingCard>

          <GlowingCard className="p-6" glowColor="purple">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-full bg-purple-500/10">
                <FolderOpen className="h-6 w-6 text-purple-500" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Outputs</p>
                <p className="text-2xl font-bold">{formatSize(summary.outputs.size_mb)}</p>
                <p className="text-xs text-muted-foreground">{summary.outputs.count} jobs</p>
              </div>
            </div>
          </GlowingCard>

          <GlowingCard className="p-6" glowColor="cyan">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-full bg-cyan-500/10">
                <HardDrive className="h-6 w-6 text-cyan-500" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Used</p>
                <p className="text-2xl font-bold">{formatSize(summary.total_size_mb)}</p>
              </div>
            </div>
          </GlowingCard>
        </div>
      )}

      {/* Quick Actions */}
      <GlowingCard className="p-4" glowColor="pink">
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-sm font-medium text-muted-foreground">Quick Actions:</span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => clearAll("uploads")}
            disabled={deleting === "uploads"}
            className="text-orange-500 border-orange-500/50 hover:bg-orange-500/10"
          >
            {deleting === "uploads" ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Trash2 className="h-4 w-4 mr-2" />
            )}
            Clear Uploads
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => clearAll("outputs")}
            disabled={deleting === "outputs"}
            className="text-orange-500 border-orange-500/50 hover:bg-orange-500/10"
          >
            {deleting === "outputs" ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Trash2 className="h-4 w-4 mr-2" />
            )}
            Clear Outputs
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={() => clearAll("all")}
            disabled={deleting === "all"}
          >
            {deleting === "all" ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <AlertTriangle className="h-4 w-4 mr-2" />
            )}
            Clear All
          </Button>
        </div>
      </GlowingCard>

      {/* Uploads List */}
      <div className="space-y-4">
        <h2 className="text-xl font-semibold flex items-center gap-2">
          <Upload className="h-5 w-5" />
          Uploaded Videos ({uploads.length})
        </h2>
        
        {uploads.length === 0 ? (
          <GlowingCard className="p-8 text-center" glowColor="blue">
            <FileVideo className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
            <p className="text-muted-foreground">No uploaded videos</p>
          </GlowingCard>
        ) : (
          <div className="space-y-2">
            {uploads.map((file, index) => (
              <motion.div
                key={file.name}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <GlowingCard className="p-4" glowColor="blue">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <FileVideo className="h-8 w-8 text-blue-500" />
                      <div>
                        <p className="font-medium truncate max-w-md">{file.name}</p>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Badge variant="secondary">{formatSize(file.size_mb)}</Badge>
                          <span>•</span>
                          <span>{formatDate(file.modified)}</span>
                        </div>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => deleteUpload(file.name)}
                      disabled={deleting === file.name}
                      className="text-destructive hover:text-destructive hover:bg-destructive/10"
                    >
                      {deleting === file.name ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </GlowingCard>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* Outputs List */}
      <div className="space-y-4">
        <h2 className="text-xl font-semibold flex items-center gap-2">
          <FolderOpen className="h-5 w-5" />
          Generated Clips ({outputs.length})
        </h2>
        
        {outputs.length === 0 ? (
          <GlowingCard className="p-8 text-center" glowColor="purple">
            <FolderOpen className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
            <p className="text-muted-foreground">No generated clips</p>
          </GlowingCard>
        ) : (
          <div className="space-y-2">
            {outputs.map((folder, index) => (
              <motion.div
                key={folder.name}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <GlowingCard className="p-4" glowColor="purple">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <FolderOpen className="h-8 w-8 text-purple-500" />
                      <div>
                        <p className="font-medium truncate max-w-md">{folder.name}</p>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Badge variant="secondary">{formatSize(folder.size_mb)}</Badge>
                          {folder.file_count && (
                            <>
                              <span>•</span>
                              <span>{folder.file_count} files</span>
                            </>
                          )}
                          <span>•</span>
                          <span>{formatDate(folder.modified)}</span>
                        </div>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => deleteOutput(folder.name)}
                      disabled={deleting === folder.name}
                      className="text-destructive hover:text-destructive hover:bg-destructive/10"
                    >
                      {deleting === folder.name ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </GlowingCard>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
