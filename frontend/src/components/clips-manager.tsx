"use client"

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { Play, Download, Settings, Trash2, Zap, Layers, Scissors, MonitorPlay } from "lucide-react";
import axios from "axios";

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
  });

  const quality_presets = [
    { id: "tiktok", name: "TikTok", icon: "smartphone" },
    { id: "instagram_reels", name: "Instagram Reels", icon: "instagram" },
    { id: "youtube_shorts", name: "YouTube Shorts", icon: "youtube" },
    { id: "youtube_standard", name: "YouTube (HD)", icon: "youtube" },
    { id: "twitter", name: "Twitter/X", icon: "twitter" },
    { id: "linkedin", name: "LinkedIn", icon: "linkedin" },
    { id: "high_quality", name: "High Quality", icon: "hd" },
    { id: "balanced", name: "Balanced", icon: "activity" },
    { id: "fast", name: "Fast Export", icon: "zap" },
  ];

  const caption_themes = [
    { id: "viral", name: "Viral", description: "Classic viral style" },
    { id: "gradient_sunset", name: "Gradient Sunset", description: "Warm sunset colors" },
    { id: "gradient_ocean", name: "Gradient Ocean", description: "Cool ocean colors" },
    { id: "neon_pink", name: "Neon Pink", description: "Glowing neon effect" },
    { id: "neon_blue", name: "Neon Blue", description: "Cool blue glow" },
    { id: "minimal", name: "Minimal", description: "Clean and simple" },
    { id: "bounce", name: "Bounce", description: "Bouncy animation" },
    { id: "wave", name: "Wave", description: "Wave animation" },
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
      // Export with selected options
      for (const clipId of selectedClips) {
        setExportStatus(prev => ({ ...prev, [clipId]: "processing" }));
        setExportProgress(prev => ({ ...prev, [clipId]: 0 }));

        // Simulate progress
        for (let i = 0; i <= 100; i += 10) {
          await new Promise(resolve => setTimeout(resolve, 100));
          setExportProgress(prev => ({ ...prev, [clipId]: i }));
        }

        setExportStatus(prev => ({ ...prev, [clipId]: "completed" }));
      }

      alert(`Successfully exported ${selectedClips.length} clips!`);
    } catch (error) {
      console.error("Export failed:", error);
      alert("Export failed. Please try again.");
    }
  };

  const handlePreviewClip = async (clipId: string) => {
    // TODO: Implement preview modal
    console.log("Preview clip:", clipId);
  };

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Clips Manager</h1>
        <p className="text-gray-600">
          Manage and export your viral clips with advanced options
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
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Quality Preset */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Quality Preset
              </label>
              <select
                className="w-full p-2 border rounded-md"
                value={exportOptions.quality_preset}
                onChange={(e) =>
                  setExportOptions({ ...exportOptions, quality_preset: e.target.value })
                }
              >
                {quality_presets.map(preset => (
                  <option key={preset.id} value={preset.id}>
                    {preset.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Caption Theme */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Caption Theme
              </label>
              <select
                className="w-full p-2 border rounded-md"
                value={exportOptions.caption_theme}
                onChange={(e) =>
                  setExportOptions({ ...exportOptions, caption_theme: e.target.value })
                }
              >
                {caption_themes.map(theme => (
                  <option key={theme.id} value={theme.id}>
                    {theme.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Caption Style */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Caption Style
              </label>
              <select
                className="w-full p-2 border rounded-md"
                value={exportOptions.caption_style}
                onChange={(e) =>
                  setExportOptions({ ...exportOptions, caption_style: e.target.value })
                }
              >
                {caption_styles.map(style => (
                  <option key={style.id} value={style.id}>
                    {style.name}
                  </option>
                ))}
              </select>
            </div>

            {/* GPU Acceleration */}
            <div>
              <label className="block text-sm font-medium mb-2">
                GPU Acceleration
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="gpu-toggle"
                  checked={exportOptions.use_gpu}
                  onChange={(e) =>
                    setExportOptions({ ...exportOptions, use_gpu: e.target.checked })
                  }
                  className="w-4 h-4"
                />
                <label htmlFor="gpu-toggle" className="text-sm">
                  Enable (if available)
                </label>
              </div>
            </div>

            {/* Add Captions */}
            <div className="col-span-1 md:col-span-2">
              <label className="block text-sm font-medium mb-2">
                Captions
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="captions-toggle"
                  checked={exportOptions.add_captions}
                  onChange={(e) =>
                    setExportOptions({ ...exportOptions, add_captions: e.target.checked })
                  }
                  className="w-4 h-4"
                />
                <label htmlFor="captions-toggle" className="text-sm">
                  Add styled captions to clips
                </label>
              </div>
            </div>
          </div>

          <Separator className="my-6" />

          {/* Export Buttons */}
          <div className="flex gap-4 justify-end">
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
                        {exportStatus[clip.id] === "completed" ? "Completed!" : "Exporting..."}
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
