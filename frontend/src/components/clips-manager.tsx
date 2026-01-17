"use client"

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Play, Download, Settings, Trash2, Zap, Layers, Scissors, MonitorPlay, Sparkles, CheckCircle, AlertCircle } from "lucide-react";
import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Clip {
  id: string;
  start_time: number;
  end_time: number;
  duration: number;
  transcript: string;
  score: number;
  semantic_score?: number;
  heuristic_score?: number;
  audio_score?: number;
  visual_score?: number;
  words: Array<{ text: string; start_time: number; end_time: number }>;
}

interface ExportOptions {
  quality_preset: string;
  add_captions: boolean;
  caption_theme: string;
  caption_style: string;
  use_gpu: boolean;
  use_scene_detection: boolean;
  use_camera_switching: boolean;
}

export default function ClipsManager() {
  const [clips, setClips] = useState<Clip[]>([]);
  const [selectedClips, setSelectedClips] = useState<string[]>([]);
  const [exportProgress, setExportProgress] = useState<{ [key: string]: number }>({});
  const [exportStatus, setExportStatus] = useState<{ [key: string]: string }>({});
  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    quality_preset: "tiktok",
    add_captions: true,
    caption_theme: "viral",
    caption_style: "karaoke",
    use_gpu: true,
    use_scene_detection: true,
    use_camera_switching: true,
  });
  const [jobId, setJobId] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const quality_presets = [
    { id: "tiktok", name: "TikTok", icon: "smartphone", description: "9:16, 60fps, 8000k" },
    { id: "instagram_reels", name: "Instagram Reels", icon: "instagram", description: "9:16, 60fps, 8000k" },
    { id: "youtube_shorts", name: "YouTube Shorts", icon: "youtube", description: "9:16, 60fps, 8000k" },
    { id: "youtube_standard", name: "YouTube (HD)", icon: "youtube", description: "16:9, 30fps, 5000k" },
    { id: "twitter", name: "Twitter/X", icon: "twitter", description: "1280x720, 30fps, 3000k" },
    { id: "linkedin", name: "LinkedIn", icon: "linkedin", description: "1280x720, 30fps, 3000k" },
    { id: "facebook", name: "Facebook", icon: "facebook", description: "1920x1080, 30fps, 4000k" },
    { id: "high_quality", name: "High Quality", icon: "hd", description: "1080p, 60fps, 10000k" },
    { id: "balanced", name: "Balanced", icon: "activity", description: "720p, 30fps, 3000k" },
    { id: "fast", name: "Fast Export", icon: "zap", description: "720p, 30fps, 2500k" },
  ];

  const caption_themes = [
    { id: "viral", name: "Viral", description: "Classic viral style" },
    { id: "gradient_sunset", name: "Gradient Sunset", description: "Warm sunset colors" },
    { id: "gradient_ocean", name: "Gradient Ocean", description: "Cool ocean colors" },
    { id: "neon_pink", name: "Neon Pink", description: "Glowing neon pink" },
    { id: "neon_blue", name: "Neon Blue", description: "Glowing neon blue" },
    { id: "minimal", name: "Minimal", description: "Clean and simple" },
    { id: "bounce", name: "Bounce", description: "Bouncy animation" },
    { id: "wave", name: "Wave", description: "Wave animation" },
    { id: "glow", name: "Glow", description: "Neon glow effect" },
  ];

  const caption_styles = [
    { id: "karaoke", name: "Karaoke", description: "Word-by-word highlighting" },
    { id: "viral", name: "Viral", description: "Classic viral captions" },
    { id: "gradient", name: "Gradient", description: "Colorful gradient transitions" },
    { id: "bounce", name: "Bounce", description: "Bouncy word animations" },
    { id: "glow", name: "Glow", description: "Neon glow effect" },
  ];

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const getScoreColor = (score: number) => {
    if (score >= 85) return "bg-green-500";
    if (score >= 70) return "bg-blue-500";
    if (score >= 55) return "bg-yellow-500";
    return "bg-gray-500";
  };

  const getScoreIcon = (score: number) => {
    if (score >= 85) return <Sparkles className="w-3 h-3 text-green-500" />;
    if (score >= 70) return <CheckCircle className="w-3 h-3 text-blue-500" />;
    return <AlertCircle className="w-3 h-3 text-yellow-500" />;
  };

  // Fetch job data on mount
  useEffect(() => {
    const fetchJobId = async () => {
      const params = new URLSearchParams(window.location.search);
      const id = params.get("job");
      if (id) {
        setJobId(id);
        await fetchJobData(id);
      }
    };

    fetchJobId();
  }, []);

  const fetchJobData = async (id: string) => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_URL}/api/upload/job/${id}`);
      if (!response.ok) throw new Error("Failed to fetch job");

      const data = await response.json();
      setClips(data.clips || []);
    } catch (err) {
      console.error("Failed to fetch job data:", err);
      setError("Failed to load clips. Make sure backend is running.");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectAll = () => {
    setSelectedClips(clips.map(c => c.id));
  };

  const handleDeselectAll = () => {
    setSelectedClips([]);
  };

  const handleToggleClip = (clipId: string) => {
    setSelectedClips(prev =>
      prev.includes(clipId)
        ? prev.filter(id => id !== clipId)
        : [...prev, clipId]
    );
  };

  const handleExportSelected = async () => {
    if (selectedClips.length === 0) {
      alert("Please select at least one clip to export");
      return;
    }

    try {
      for (const clipId of selectedClips) {
        setExportStatus(prev => ({ ...prev, [clipId]: "processing" }));
        setExportProgress(prev => ({ ...prev, [clipId]: 0 }));

        // Start export via API
        const response = await fetch(`${API_URL}/api/clips/${jobId}/export/${clipId}`, {
          method: "POST",
        });

        if (!response.ok) {
          throw new Error(`Export failed: ${response.statusText}`);
        }

        const data = await response.json();
        const exportId = data.export_id;

        // Poll for export progress
        let completed = false;
        let failed = false;

        while (!completed && !failed) {
          await new Promise(resolve => setTimeout(resolve, 1000));

          const statusResponse = await fetch(`${API_URL}/api/clips/export/${exportId}/status`);
          if (!statusResponse.ok) {
            throw new Error("Failed to get export status");
          }

          const statusData = await statusResponse.json();
          setExportProgress(prev => ({ ...prev, [clipId]: statusData.progress }));

          if (statusData.status === "completed") {
            completed = true;
            setExportProgress(prev => ({ ...prev, [clipId]: 100 }));
            setExportStatus(prev => ({ ...prev, [clipId]: "completed" }));

            // Trigger download
            window.open(`${API_URL}/api/clips/export/${exportId}/download`, '_blank');
          } else if (statusData.status === "failed") {
            failed = true;
            setExportStatus(prev => ({ ...prev, [clipId]: "failed" }));
            throw new Error(statusData.message || "Export failed");
          }
        }
      }

      alert(`Successfully exported ${selectedClips.length} clips!`);
    } catch (err) {
      console.error("Export failed:", err);
      alert(`Export failed: ${err instanceof Error ? err.message : "Unknown error"}`);
      selectedClips.forEach(clipId => {
        setExportStatus(prev => ({ ...prev, [clipId]: "failed" }));
      });
    }
  };

  const handlePreviewClip = async (clipId: string) => {
    try {
      const response = await fetch(`${API_URL}/api/clips/${jobId}/preview/${clipId}?with_subtitles=${exportOptions.add_captions}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });

      if (!response.ok) throw new Error("Preview generation failed");

      const data = await response.json();
      if (data.url) {
        // Open preview in new tab
        window.open(`${API_URL}${data.url}`, '_blank');
      } else {
        alert("Failed to generate preview");
      }
    } catch (err) {
      console.error("Preview error:", err);
      alert("Failed to generate preview. Make sure backend is running.");
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6 max-w-7xl">
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Clips Manager</h1>
          <p className="text-gray-600">Loading clips...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-6 max-w-7xl">
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Error</h1>
          <p className="text-red-600">{error}</p>
          <Button onClick={() => window.location.reload()} className="mt-4">
            Retry
          </Button>
        </div>
      </div>
    );
  }

  if (!jobId) {
    return (
      <div className="container mx-auto p-6 max-w-7xl">
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">No Job Selected</h1>
          <p className="text-gray-600">Please select a job from the dashboard first.</p>
          <Button onClick={() => window.location.href = "/dashboard"}>
            Go to Dashboard
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Clips Manager</h1>
        <p className="text-gray-600">
          Manage and export your viral clips with advanced AI features
        </p>
      </div>

      {/* Export Options */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Export Settings
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Quality Preset */}
            <div>
              <Label className="block text-sm font-medium mb-2">
                Quality Preset
              </Label>
              <Select
                value={exportOptions.quality_preset}
                onValueChange={(value: string) => setExportOptions({ ...exportOptions, quality_preset: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {quality_presets.map(preset => (
                    <SelectItem key={preset.id} value={preset.id}>
                      <div className="flex items-center gap-2">
                        <Scissors className="w-4 h-4" />
                        <div>
                          <div className="font-medium">{preset.name}</div>
                          <div className="text-xs text-gray-500">{preset.description}</div>
                        </div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Caption Theme */}
            <div>
              <Label className="block text-sm font-medium mb-2">
                Caption Theme
              </Label>
              <Select
                value={exportOptions.caption_theme}
                onValueChange={(value: string) => setExportOptions({ ...exportOptions, caption_theme: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {caption_themes.map(theme => (
                    <SelectItem key={theme.id} value={theme.id}>
                      <div className="flex items-center gap-2">
                        <Sparkles className="w-4 h-4" />
                        <div>
                          <div className="font-medium">{theme.name}</div>
                          <div className="text-xs text-gray-500">{theme.description}</div>
                        </div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Caption Style */}
            <div>
              <Label className="block text-sm font-medium mb-2">
                Caption Style
              </Label>
              <Select
                value={exportOptions.caption_style}
                onValueChange={(value: string) => setExportOptions({ ...exportOptions, caption_style: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {caption_styles.map(style => (
                    <SelectItem key={style.id} value={style.id}>
                      <div>
                        <div className="font-medium">{style.name}</div>
                        <div className="text-xs text-gray-500">{style.description}</div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* GPU Acceleration */}
            <div className="flex flex-col gap-2">
              <Label className="block text-sm font-medium">
                GPU Acceleration
              </Label>
              <div className="flex items-center gap-2">
                <Switch
                  checked={exportOptions.use_gpu}
                  onCheckedChange={(checked: boolean) => setExportOptions({ ...exportOptions, use_gpu: checked })}
                />
                <span className="text-sm text-gray-600">
                  {exportOptions.use_gpu ? "Enabled" : "Disabled"}
                </span>
              </div>
            </div>

            {/* Scene Detection */}
            <div className="flex flex-col gap-2">
              <Label className="block text-sm font-medium">
                Scene Detection
              </Label>
              <div className="flex items-center gap-2">
                <Switch
                  checked={exportOptions.use_scene_detection}
                  onCheckedChange={(checked: boolean) => setExportOptions({ ...exportOptions, use_scene_detection: checked })}
                />
                <span className="text-sm text-gray-600">
                  {exportOptions.use_scene_detection ? "Enabled" : "Disabled"}
                </span>
              </div>
            </div>

            {/* Camera Switching */}
            <div className="flex flex-col gap-2">
              <Label className="block text-sm font-medium">
                Camera Switching
              </Label>
              <div className="flex items-center gap-2">
                <Switch
                  checked={exportOptions.use_camera_switching}
                  onCheckedChange={(checked: boolean) => setExportOptions({ ...exportOptions, use_camera_switching: checked })}
                />
                <span className="text-sm text-gray-600">
                  {exportOptions.use_camera_switching ? "Enabled" : "Disabled"}
                </span>
              </div>
            </div>
          </div>

          <Separator className="my-6" />

          {/* Caption Toggle */}
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2">
              <Switch
                checked={exportOptions.add_captions}
                onCheckedChange={(checked: boolean) => setExportOptions({ ...exportOptions, add_captions: checked })}
              />
              <span className="text-sm font-medium">Add Styled Captions</span>
            </div>
            <p className="text-sm text-gray-500">
              Enhances clips with AI-generated animated captions
            </p>
          </div>

          {/* Export Buttons */}
          <div className="flex gap-4 justify-end mt-4">
            <Button variant="outline" onClick={handleDeselectAll}>
              Deselect All
            </Button>
            <Button onClick={handleExportSelected} disabled={selectedClips.length === 0}>
              <Download className="w-4 h-4 mr-2" />
              Export Selected ({selectedClips.length})
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Clips List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex gap-4">
            <h2 className="text-xl font-semibold">
              All Clips ({clips.length})
            </h2>
            <Badge variant="secondary">
              {selectedClips.length} selected
            </Badge>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleSelectAll}>
              Select All
            </Button>
            <Button variant="outline" size="sm" onClick={handleDeselectAll}>
              Deselect All
            </Button>
          </div>
        </div>

        {/* Clips Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {clips.map((clip, index) => (
            <Card
              key={clip.id}
              className={`cursor-pointer transition-all hover:shadow-lg ${
                selectedClips.includes(clip.id)
                  ? "ring-2 ring-blue-500 shadow-lg"
                  : "hover:ring-1 hover:ring-blue-300"
              }`}
              onClick={() => handleToggleClip(clip.id)}
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <CardTitle className="text-base font-semibold pr-4">
                    Clip #{index + 1}
                  </CardTitle>
                  <input
                    type="checkbox"
                    checked={selectedClips.includes(clip.id)}
                    onChange={() => handleToggleClip(clip.id)}
                    className="w-5 h-5 cursor-pointer"
                    onClick={(e) => e.stopPropagation()}
                  />
                </div>
              </CardHeader>
              <CardContent>
                {/* Score Badge */}
                <div className="mb-3">
                  <Badge
                    className={`${getScoreColor(clip.score)} text-white`}
                  >
                    <Zap className="w-3 h-3 mr-1 inline" />
                    Score: {clip.score.toFixed(1)}
                  </Badge>
                </div>

                {/* Score Breakdown */}
                <div className="grid grid-cols-2 gap-2 mb-3 text-xs">
                  <div>
                    <span className="text-gray-600">Semantic:</span>{" "}
                    <span className="font-medium">
                      {(clip.semantic_score || 0).toFixed(1)}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Heuristic:</span>{" "}
                    <span className="font-medium">
                      {(clip.heuristic_score || 0).toFixed(1)}
                    </span>
                  </div>
                  {clip.audio_score !== undefined && (
                    <div>
                      <span className="text-gray-600">Audio:</span>{" "}
                      <span className="font-medium">
                        {clip.audio_score.toFixed(1)}
                      </span>
                    </div>
                  )}
                  {clip.visual_score !== undefined && (
                    <div>
                      <span className="text-gray-600">Visual:</span>{" "}
                      <span className="font-medium">
                        {clip.visual_score.toFixed(1)}
                      </span>
                    </div>
                  )}
                </div>

                {/* Transcript */}
                <div className="mb-3 p-3 bg-gray-50 rounded-md">
                  <p className="text-sm text-gray-700 line-clamp-3">
                    {clip.transcript}
                  </p>
                </div>

                {/* Duration */}
                <div className="flex items-center gap-2 text-sm text-gray-600 mb-3">
                  <MonitorPlay className="w-4 h-4" />
                  <span>{formatTime(clip.duration)}</span>
                  <span>•</span>
                  <span>
                    {formatTime(clip.start_time)} - {formatTime(clip.end_time)}
                  </span>
                </div>

                {/* Export Progress */}
                {exportStatus[clip.id] && (
                  <div className="mb-3">
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-medium">
                        {exportStatus[clip.id] === "completed"
                          ? "Completed!"
                          : "Exporting..."}
                      </span>
                      <span className="text-gray-600">
                        {exportProgress[clip.id] || 0}%
                      </span>
                    </div>
                    <Progress value={exportProgress[clip.id] || 0} />
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    className="flex-1"
                    onClick={(e) => {
                      e.stopPropagation();
                      handlePreviewClip(clip.id);
                    }}
                  >
                    <Play className="w-4 h-4 mr-1" />
                    Preview
                  </Button>
                  <Button
                    size="sm"
                    className="flex-1"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleToggleClip(clip.id);
                      setTimeout(() => handleExportSelected(), 100);
                    }}
                    disabled={
                      exportStatus[clip.id] === "processing" ||
                      exportStatus[clip.id] === "completed"
                    }
                  >
                    {exportStatus[clip.id] === "completed" ? (
                      <>
                        <Download className="w-4 h-4 mr-1" />
                        Download
                      </>
                    ) : (
                      <>
                        <Download className="w-4 h-4 mr-1" />
                        Export
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
