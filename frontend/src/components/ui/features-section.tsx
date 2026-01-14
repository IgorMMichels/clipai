"use client";

import { motion } from "framer-motion";
import { 
  Scissors, 
  Sparkles, 
  Languages, 
  Smartphone, 
  Wand2, 
  Zap,
  FileVideo,
  MessageSquare
} from "lucide-react";
import { GlowingGridItem } from "./glowing-card";

const features = [
  {
    icon: <Scissors className="h-5 w-5 text-primary" />,
    title: "AI Clip Detection",
    description: "Automatically finds the most engaging moments in your videos using advanced NLP algorithms.",
    glowColor: "purple",
    area: "md:col-span-1",
  },
  {
    icon: <Smartphone className="h-5 w-5 text-primary" />,
    title: "Smart Resizing",
    description: "Convert 16:9 videos to 9:16 for TikTok, Reels, and Shorts with speaker tracking.",
    glowColor: "blue",
    area: "md:col-span-1",
  },
  {
    icon: <Sparkles className="h-5 w-5 text-primary" />,
    title: "Transcription",
    description: "Accurate transcription with word-level timestamps using WhisperX.",
    glowColor: "cyan",
    area: "md:col-span-1",
  },
  {
    icon: <Languages className="h-5 w-5 text-primary" />,
    title: "Multi-Language",
    description: "Generate descriptions in English and Portuguese. More languages coming soon.",
    glowColor: "pink",
    area: "md:col-span-1",
  },
  {
    icon: <Wand2 className="h-5 w-5 text-primary" />,
    title: "Effects & Music",
    description: "Add background music, transitions, and intro text to your clips.",
    glowColor: "purple",
    area: "md:col-span-1",
  },
  {
    icon: <MessageSquare className="h-5 w-5 text-primary" />,
    title: "AI Descriptions",
    description: "Generate viral-ready captions with hashtags using GPT or Claude.",
    glowColor: "blue",
    area: "md:col-span-1",
  },
  {
    icon: <FileVideo className="h-5 w-5 text-primary" />,
    title: "Batch Processing",
    description: "Process multiple videos at once. Queue and manage all your clips.",
    glowColor: "cyan",
    area: "md:col-span-2",
  },
  {
    icon: <Zap className="h-5 w-5 text-primary" />,
    title: "Lightning Fast",
    description: "Optimized processing pipeline. Get your clips in minutes, not hours.",
    glowColor: "pink",
    area: "md:col-span-1",
  },
];

export function FeaturesSection() {
  return (
    <section className="py-24 px-4 md:px-6 relative overflow-hidden bg-background">
      {/* Background elements */}
      <div className="absolute inset-0 bg-grid" />
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-[oklch(0.7_0.25_270_/_10%)] rounded-full blur-3xl" />
      
      <div className="relative z-10 container mx-auto max-w-7xl">
        {/* Section header */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          whileInView={{ y: 0, opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-5xl font-bold tracking-tight mb-4">
            Everything You Need to
            <span className="text-gradient"> Create Viral Clips</span>
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Powerful AI tools to transform your long-form content into engaging short clips
            optimized for every social media platform.
          </p>
        </motion.div>

        {/* Features grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 lg:gap-6">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ y: 20, opacity: 0 }}
              whileInView={{ y: 0, opacity: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className={feature.area}
            >
              <GlowingGridItem
                icon={feature.icon}
                title={feature.title}
                description={feature.description}
                glowColor={feature.glowColor}
                className="h-full"
              />
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
