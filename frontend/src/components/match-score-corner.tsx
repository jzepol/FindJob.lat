"use client";

import { Sparkles } from "lucide-react";
import { matchScoreStyles } from "@/lib/match-score";
import { cn } from "@/lib/utils";

export function MatchScoreCorner({
  score,
  className,
}: {
  score: number;
  className?: string;
}) {
  const s = matchScoreStyles(score);

  return (
    <div
      className={cn(
        "pointer-events-none absolute right-3 top-3 z-10 flex flex-col items-center rounded-2xl border border-white/10 px-3 py-2 backdrop-blur-md",
        "ring-2",
        s.ring,
        s.bg,
        s.glow,
        className,
      )}
      aria-label={`${score}% de compatibilidad con tu CV`}
    >
      <Sparkles className={cn("mb-0.5 h-3.5 w-3.5", s.text)} />
      <span className={cn("font-mono text-2xl font-bold leading-none tracking-tight", s.text)}>
        {score}
        <span className="text-sm font-semibold">%</span>
      </span>
      <span className={cn("mt-1 text-[9px] font-semibold uppercase tracking-widest", s.text)}>
        {s.label}
      </span>
    </div>
  );
}