export function matchScoreStyles(score: number): {
  ring: string;
  bg: string;
  text: string;
  glow: string;
  label: string;
} {
  if (score >= 75) {
    return {
      ring: "ring-emerald-400/50",
      bg: "bg-gradient-to-br from-emerald-500/25 via-emerald-500/10 to-transparent",
      text: "text-emerald-300",
      glow: "shadow-[0_0_24px_-4px_rgba(52,211,153,0.45)]",
      label: "Muy compatible",
    };
  }
  if (score >= 55) {
    return {
      ring: "ring-primary/50",
      bg: "bg-gradient-to-br from-primary/25 via-primary/10 to-transparent",
      text: "text-primary",
      glow: "shadow-[0_0_24px_-4px_rgba(20,184,166,0.4)]",
      label: "Compatible",
    };
  }
  return {
    ring: "ring-border",
    bg: "bg-gradient-to-br from-surface-2 to-transparent",
    text: "text-foreground-secondary",
    glow: "shadow-md",
    label: "Match",
  };
}