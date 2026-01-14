"use client";

import { motion } from "framer-motion";
import { 
  Upload, 
  Scissors, 
  Clock, 
  TrendingUp,
  FileVideo,
  Sparkles,
  ArrowRight,
} from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { GlowingCard } from "@/components/ui/glowing-card";

const stats = [
  {
    title: "Videos Processed",
    value: "0",
    icon: FileVideo,
    color: "purple",
  },
  {
    title: "Clips Generated",
    value: "0",
    icon: Scissors,
    color: "blue",
  },
  {
    title: "Processing Time",
    value: "0m",
    icon: Clock,
    color: "cyan",
  },
  {
    title: "Success Rate",
    value: "100%",
    icon: TrendingUp,
    color: "pink",
  },
];

export default function DashboardPage() {
  return (
    <div className="p-6 lg:p-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Welcome back! Ready to create some viral clips?
          </p>
        </div>
        <Link href="/dashboard/upload">
          <Button size="lg" className="glow-purple">
            <Upload className="mr-2 h-4 w-4" />
            Upload Video
          </Button>
        </Link>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, index) => (
          <motion.div
            key={stat.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <GlowingCard className="p-6" glowColor={stat.color}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">{stat.title}</p>
                  <p className="text-3xl font-bold mt-1">{stat.value}</p>
                </div>
                <div className="rounded-full bg-primary/10 p-3">
                  <stat.icon className="h-6 w-6 text-primary" />
                </div>
              </div>
            </GlowingCard>
          </motion.div>
        ))}
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upload card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <GlowingCard className="p-8" glowColor="purple">
            <div className="flex flex-col items-center text-center space-y-4">
              <div className="rounded-full bg-primary/10 p-4">
                <Upload className="h-8 w-8 text-primary" />
              </div>
              <div>
                <h3 className="text-xl font-semibold">Upload Your First Video</h3>
                <p className="text-muted-foreground mt-1">
                  Drop a video and let AI find the best clips automatically
                </p>
              </div>
              <Link href="/dashboard/upload">
                <Button>
                  Get Started
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </div>
          </GlowingCard>
        </motion.div>

        {/* Features highlight */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <GlowingCard className="p-8" glowColor="blue">
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="rounded-full bg-primary/10 p-3">
                  <Sparkles className="h-6 w-6 text-primary" />
                </div>
                <h3 className="text-xl font-semibold">AI-Powered Features</h3>
              </div>
              <ul className="space-y-3">
                {[
                  "Automatic clip detection with TextTiling",
                  "Smart speaker tracking for vertical videos",
                  "AI-generated descriptions in EN/PT",
                  "One-click export for all platforms",
                ].map((feature, i) => (
                  <li key={i} className="flex items-center gap-2 text-muted-foreground">
                    <div className="h-1.5 w-1.5 rounded-full bg-primary" />
                    {feature}
                  </li>
                ))}
              </ul>
            </div>
          </GlowingCard>
        </motion.div>
      </div>

      {/* Recent activity placeholder */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
      >
        <GlowingCard className="p-6" glowColor="cyan">
          <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>
          <div className="flex items-center justify-center py-12 text-muted-foreground">
            <div className="text-center">
              <FileVideo className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>No recent activity</p>
              <p className="text-sm">Upload a video to get started</p>
            </div>
          </div>
        </GlowingCard>
      </motion.div>
    </div>
  );
}
