"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { VideoUpload } from "@/components/ui/video-upload";
import { GlowingCard } from "@/components/ui/glowing-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Languages,
  Smartphone,
  Sparkles,
  Music,
  Subtitles,
  Settings2,
} from "lucide-react";

export default function UploadPage() {
  const router = useRouter();
  const [settings, setSettings] = useState({
    language: "auto",
    aspectRatio: "9:16",
    generateDescription: true,
    descriptionLanguage: "en",
    addMusic: false,
    addSubtitles: true,
  });

  const handleUploadComplete = (jobId: string) => {
    router.push(`/dashboard/clips?job=${jobId}`);
  };

  const aspectRatios = [
    { label: "9:16", value: "9:16", desc: "TikTok, Reels, Shorts" },
    { label: "1:1", value: "1:1", desc: "Instagram, Facebook" },
    { label: "16:9", value: "16:9", desc: "YouTube, Twitter" },
    { label: "4:5", value: "4:5", desc: "Instagram Feed" },
  ];

  return (
    <div className="p-6 lg:p-8 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Upload Video</h1>
        <p className="text-muted-foreground mt-1">
          Upload your video and configure processing options
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload zone */}
        <div className="lg:col-span-2">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <VideoUpload onUploadComplete={handleUploadComplete} settings={settings} />
          </motion.div>
        </div>

        {/* Settings panel */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="space-y-4"
        >
          {/* Aspect Ratio */}
          <GlowingCard className="p-5" glowColor="purple">
            <div className="flex items-center gap-2 mb-4">
              <Smartphone className="h-5 w-5 text-primary" />
              <h3 className="font-semibold">Aspect Ratio</h3>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {aspectRatios.map((ratio) => (
                <Button
                  key={ratio.value}
                  variant={settings.aspectRatio === ratio.value ? "default" : "outline"}
                  className="h-auto py-3 flex-col"
                  onClick={() => setSettings({ ...settings, aspectRatio: ratio.value })}
                >
                  <span className="font-bold">{ratio.label}</span>
                  <span className="text-xs opacity-70">{ratio.desc}</span>
                </Button>
              ))}
            </div>
          </GlowingCard>

          {/* Language */}
          <GlowingCard className="p-5" glowColor="blue">
            <div className="flex items-center gap-2 mb-4">
              <Languages className="h-5 w-5 text-primary" />
              <h3 className="font-semibold">Language</h3>
            </div>
            <div className="space-y-3">
              <div>
                <p className="text-sm text-muted-foreground mb-2">Video Language</p>
                <div className="flex gap-2">
                  {["auto", "en", "pt"].map((lang) => (
                    <Button
                      key={lang}
                      variant={settings.language === lang ? "default" : "outline"}
                      size="sm"
                      onClick={() => setSettings({ ...settings, language: lang })}
                    >
                      {lang === "auto" ? "Auto Detect" : lang.toUpperCase()}
                    </Button>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-sm text-muted-foreground mb-2">Description Language</p>
                <div className="flex gap-2">
                  {["en", "pt"].map((lang) => (
                    <Button
                      key={lang}
                      variant={settings.descriptionLanguage === lang ? "default" : "outline"}
                      size="sm"
                      onClick={() => setSettings({ ...settings, descriptionLanguage: lang })}
                    >
                      {lang === "en" ? "English" : "Portuguese"}
                    </Button>
                  ))}
                </div>
              </div>
            </div>
          </GlowingCard>

          {/* AI Features */}
          <GlowingCard className="p-5" glowColor="cyan">
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="h-5 w-5 text-primary" />
              <h3 className="font-semibold">AI Features</h3>
            </div>
            <div className="space-y-3">
              <button
                className="w-full flex items-center justify-between p-3 rounded-lg hover:bg-accent/50 transition-colors"
                onClick={() => setSettings({ ...settings, generateDescription: !settings.generateDescription })}
              >
                <div className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4" />
                  <span className="text-sm">AI Descriptions</span>
                </div>
                <Badge variant={settings.generateDescription ? "default" : "secondary"}>
                  {settings.generateDescription ? "ON" : "OFF"}
                </Badge>
              </button>
              <button
                className="w-full flex items-center justify-between p-3 rounded-lg hover:bg-accent/50 transition-colors"
                onClick={() => setSettings({ ...settings, addSubtitles: !settings.addSubtitles })}
              >
                <div className="flex items-center gap-2">
                  <Subtitles className="h-4 w-4" />
                  <span className="text-sm">Auto Subtitles</span>
                </div>
                <Badge variant={settings.addSubtitles ? "default" : "secondary"}>
                  {settings.addSubtitles ? "ON" : "OFF"}
                </Badge>
              </button>
              <button
                className="w-full flex items-center justify-between p-3 rounded-lg hover:bg-accent/50 transition-colors"
                onClick={() => setSettings({ ...settings, addMusic: !settings.addMusic })}
              >
                <div className="flex items-center gap-2">
                  <Music className="h-4 w-4" />
                  <span className="text-sm">Background Music</span>
                </div>
                <Badge variant={settings.addMusic ? "default" : "secondary"}>
                  {settings.addMusic ? "ON" : "OFF"}
                </Badge>
              </button>
            </div>
          </GlowingCard>

          {/* Info */}
          <div className="p-4 rounded-lg border border-border bg-muted/30">
            <div className="flex items-start gap-2">
              <Settings2 className="h-4 w-4 mt-0.5 text-muted-foreground" />
              <div className="text-xs text-muted-foreground">
                <p className="font-medium">Processing Info</p>
                <p className="mt-1">
                  Videos are processed locally. For best results, use videos with clear speech.
                </p>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
