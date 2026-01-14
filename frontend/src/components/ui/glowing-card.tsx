"use client";

import { ReactNode, useRef, useState } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface GlowingCardProps {
  children: ReactNode;
  className?: string;
  glowColor?: string;
}

export function GlowingCard({ children, className, glowColor = "purple" }: GlowingCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    setMousePosition({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
  };

  const glowColors = {
    purple: "rgba(139, 92, 246, 0.5)",
    blue: "rgba(59, 130, 246, 0.5)",
    cyan: "rgba(34, 211, 238, 0.5)",
    pink: "rgba(236, 72, 153, 0.5)",
  };

  return (
    <motion.div
      ref={cardRef}
      className={cn(
        "relative rounded-2xl border border-border/50 bg-card/50 backdrop-blur-sm overflow-hidden",
        className
      )}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      whileHover={{ scale: 1.02 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
    >
      {/* Glow effect */}
      <div
        className="pointer-events-none absolute inset-0 transition-opacity duration-300"
        style={{
          opacity: isHovered ? 1 : 0,
          background: `radial-gradient(400px circle at ${mousePosition.x}px ${mousePosition.y}px, ${glowColors[glowColor as keyof typeof glowColors] || glowColors.purple}, transparent 40%)`,
        }}
      />
      
      {/* Border glow */}
      <div
        className="pointer-events-none absolute inset-0 rounded-2xl transition-opacity duration-300"
        style={{
          opacity: isHovered ? 1 : 0,
          background: `radial-gradient(200px circle at ${mousePosition.x}px ${mousePosition.y}px, ${glowColors[glowColor as keyof typeof glowColors] || glowColors.purple}, transparent 40%)`,
          mask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
          maskComposite: "xor",
          WebkitMaskComposite: "xor",
          padding: "1px",
        }}
      />

      {/* Content */}
      <div className="relative z-10">{children}</div>
    </motion.div>
  );
}

interface GlowingGridItemProps {
  icon: ReactNode;
  title: string;
  description: string;
  className?: string;
  glowColor?: string;
}

export function GlowingGridItem({ icon, title, description, className, glowColor }: GlowingGridItemProps) {
  return (
    <GlowingCard className={cn("min-h-[14rem] p-6", className)} glowColor={glowColor}>
      <div className="flex flex-col justify-between h-full gap-4">
        <div className="w-fit rounded-lg border border-border bg-muted p-3">
          {icon}
        </div>
        <div className="space-y-2">
          <h3 className="text-xl font-semibold tracking-tight">{title}</h3>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>
      </div>
    </GlowingCard>
  );
}
