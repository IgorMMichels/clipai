import { HeroSection } from "@/components/ui/hero-section";
import { FeaturesSection } from "@/components/ui/features-section";

export default function Home() {
  return (
    <main className="min-h-screen bg-background text-foreground">
      <HeroSection />
      <FeaturesSection />
      
      {/* Footer */}
      <footer className="py-12 px-4 border-t border-border bg-background">
        <div className="container mx-auto max-w-7xl text-center">
          <p className="text-sm text-muted-foreground">
            Built with ClipsAI, Next.js, and FastAPI. Open source on GitHub.
          </p>
          <p className="text-xs text-muted-foreground/60 mt-2">
            ClipAI - Transform your videos into viral clips.
          </p>
        </div>
      </footer>
    </main>
  );
}
