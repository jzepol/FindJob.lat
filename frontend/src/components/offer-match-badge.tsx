"use client";

import { Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { useAuth } from "@/components/auth-provider";
import { authenticatedFetchInit } from "@/lib/auth";
import { matchScoreStyles } from "@/lib/match-score";
import { cn } from "@/lib/utils";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export function OfferMatchBadge({
  offerId,
  variant = "inline",
}: {
  offerId: string;
  variant?: "inline" | "sidebar";
}) {
  const { user, loading: authLoading } = useAuth();
  const [score, setScore] = useState<number | null>(null);
  const hasCv = Boolean(user?.profile?.cv_text && user.profile.cv_text.length > 50);

  useEffect(() => {
    if (authLoading || !user || !hasCv) return;

    let cancelled = false;
    fetch(`${API_BASE}/offers/${offerId}`, authenticatedFetchInit())
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (!cancelled && data?.match_score != null) {
          setScore(data.match_score);
        }
      })
      .catch(() => {});

    return () => {
      cancelled = true;
    };
  }, [offerId, user, hasCv, authLoading]);

  if (authLoading || !hasCv || score === null) {
    return null;
  }

  const s = matchScoreStyles(score);

  if (variant === "sidebar") {
    return (
      <div
        className={cn(
          "mb-4 rounded-2xl border border-white/10 p-5 text-center ring-2 backdrop-blur-sm",
          s.ring,
          s.bg,
          s.glow,
        )}
      >
        <div className={cn("mb-2 flex items-center justify-center gap-1.5 text-xs font-semibold uppercase tracking-widest", s.text)}>
          <Sparkles className="h-4 w-4" />
          Tu CV
        </div>
        <p className={cn("font-mono text-5xl font-bold leading-none", s.text)}>
          {score}
          <span className="text-2xl">%</span>
        </p>
        <p className={cn("mt-2 text-sm font-medium", s.text)}>{s.label}</p>
      </div>
    );
  }

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-xl border border-white/10 px-3 py-1.5 text-sm font-bold ring-2 backdrop-blur-sm",
        s.ring,
        s.bg,
        s.text,
        s.glow,
      )}
    >
      <Sparkles className="h-4 w-4" />
      {score}% match
    </span>
  );
}