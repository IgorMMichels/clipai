"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { GlowingCard } from "@/components/ui/glowing-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Key,
  Globe,
  Palette,
  Bell,
  Save,
  Eye,
  EyeOff,
} from "lucide-react";

export default function SettingsPage() {
  const [showToken, setShowToken] = useState(false);
  const [showGeminiKey, setShowGeminiKey] = useState(false);
  const [saved, setSaved] = useState(false);
  const [settings, setSettings] = useState({
    huggingfaceToken: "",
    googleApiKey: "",
    openaiKey: "",
    anthropicKey: "",
    defaultLanguage: "en",
    theme: "dark",
    notifications: true,
  });

  // Load settings from localStorage on mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      const savedSettings = localStorage.getItem("clipai_settings");
      if (savedSettings) {
        try {
          setSettings(JSON.parse(savedSettings));
        } catch (e) {
          console.error("Failed to load settings:", e);
        }
      }
    }
  }, []);

  const handleSave = () => {
    if (typeof window !== "undefined") {
      localStorage.setItem("clipai_settings", JSON.stringify(settings));
    }
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground mt-1">
          Configure your ClipAI preferences and API keys
        </p>
      </div>

      {/* API Keys */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <GlowingCard className="p-6" glowColor="purple">
          <div className="flex items-center gap-2 mb-6">
            <Key className="h-5 w-5 text-primary" />
            <h2 className="text-xl font-semibold">API Keys</h2>
          </div>

          <div className="space-y-4">
            {/* HuggingFace Token */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                HuggingFace Token
                <Badge variant="secondary" className="ml-2">Required for Resize</Badge>
              </label>
              <div className="relative">
                <input
                  type={showToken ? "text" : "password"}
                  value={settings.huggingfaceToken}
                  onChange={(e) => setSettings({ ...settings, huggingfaceToken: e.target.value })}
                  placeholder="hf_..."
                  className="w-full px-4 py-2 pr-12 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                />
                <button
                  type="button"
                  onClick={() => setShowToken(!showToken)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showToken ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Get your token from{" "}
                <a href="https://huggingface.co/settings/tokens" target="_blank" className="text-primary hover:underline">
                  HuggingFace Settings
                </a>
              </p>
            </div>

            {/* Google Gemini API Key */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                Google Gemini API Key
                <Badge variant="default" className="ml-2">Recommended</Badge>
              </label>
              <div className="relative">
                <input
                  type={showGeminiKey ? "text" : "password"}
                  value={settings.googleApiKey}
                  onChange={(e) => setSettings({ ...settings, googleApiKey: e.target.value })}
                  placeholder="AIza..."
                  className="w-full px-4 py-2 pr-12 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                />
                <button
                  type="button"
                  onClick={() => setShowGeminiKey(!showGeminiKey)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showGeminiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Free tier available! Get from{" "}
                <a href="https://aistudio.google.com/app/apikey" target="_blank" className="text-primary hover:underline">
                  Google AI Studio
                </a>
              </p>
            </div>

            {/* OpenAI Key */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                OpenAI API Key
                <Badge variant="secondary" className="ml-2">Optional</Badge>
              </label>
              <input
                type="password"
                value={settings.openaiKey}
                onChange={(e) => setSettings({ ...settings, openaiKey: e.target.value })}
                placeholder="sk-..."
                className="w-full px-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Used for AI description generation. Get from{" "}
                <a href="https://platform.openai.com/api-keys" target="_blank" className="text-primary hover:underline">
                  OpenAI Platform
                </a>
              </p>
            </div>

            {/* Anthropic Key */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                Anthropic API Key
                <Badge variant="secondary" className="ml-2">Optional</Badge>
              </label>
              <input
                type="password"
                value={settings.anthropicKey}
                onChange={(e) => setSettings({ ...settings, anthropicKey: e.target.value })}
                placeholder="sk-ant-..."
                className="w-full px-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Alternative to OpenAI. Get from{" "}
                <a href="https://console.anthropic.com/" target="_blank" className="text-primary hover:underline">
                  Anthropic Console
                </a>
              </p>
            </div>
          </div>
        </GlowingCard>
      </motion.div>

      {/* Preferences */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <GlowingCard className="p-6" glowColor="blue">
          <div className="flex items-center gap-2 mb-6">
            <Globe className="h-5 w-5 text-primary" />
            <h2 className="text-xl font-semibold">Preferences</h2>
          </div>

          <div className="space-y-4">
            {/* Default Language */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                Default Description Language
              </label>
              <div className="flex gap-2">
                {[
                  { value: "en", label: "English" },
                  { value: "pt", label: "Portuguese" },
                ].map((lang) => (
                  <Button
                    key={lang.value}
                    variant={settings.defaultLanguage === lang.value ? "default" : "outline"}
                    onClick={() => setSettings({ ...settings, defaultLanguage: lang.value })}
                  >
                    {lang.label}
                  </Button>
                ))}
              </div>
            </div>

            {/* Theme */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                Theme
              </label>
              <div className="flex gap-2">
                {[
                  { value: "dark", label: "Dark" },
                  { value: "light", label: "Light" },
                  { value: "system", label: "System" },
                ].map((theme) => (
                  <Button
                    key={theme.value}
                    variant={settings.theme === theme.value ? "default" : "outline"}
                    onClick={() => setSettings({ ...settings, theme: theme.value })}
                  >
                    {theme.label}
                  </Button>
                ))}
              </div>
            </div>

            {/* Notifications */}
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">Notifications</p>
                <p className="text-xs text-muted-foreground">
                  Get notified when processing completes
                </p>
              </div>
              <Button
                variant={settings.notifications ? "default" : "outline"}
                size="sm"
                onClick={() => setSettings({ ...settings, notifications: !settings.notifications })}
              >
                {settings.notifications ? "Enabled" : "Disabled"}
              </Button>
            </div>
          </div>
        </GlowingCard>
      </motion.div>

      {/* Save button */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Button size="lg" onClick={handleSave} className="w-full md:w-auto glow-purple">
          <Save className="h-4 w-4 mr-2" />
          {saved ? "Saved!" : "Save Settings"}
        </Button>
      </motion.div>
    </div>
  );
}
