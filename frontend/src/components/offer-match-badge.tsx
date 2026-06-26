"use client";

import { Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { useAuth } from "@/components/auth-provider";
import { authenticatedFetchInit } from "@/lib/auth";
import { cn } from "@/lib/utils";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

function matchScoreColor(score: number): string {
  if (score >= 75) return "border-emerald-500/30 bg-emerald-500/10 text-emerald-400";
  if (score >= 55) return "border-primary/30 bg-primary/10 text-primary";
  return "border-border bg-surface-2 text-muted";
}

function matchLabel(score: number): string {
  if (score >= 75) return "Muy compatible";
  if (score >= 55) return "Compatible";
  return "Match parcial";
}

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

  if (variant === "sidebar") {
    return (
      <div
        className={cn(
          "mb-4 rounded-xl border p-4 text-center",
          matchScoreColor(score),
        )}
      >
        <div className="mb-1 flex items-center justify-center gap-1.5 text-xs font-medium uppercase tracking-wide opacity-80">
          <Sparkles className="h-3.5 w-3.5" />
          Compatibilidad con tu CV
        </div>
        <p className="font-mono text-4xl font-bold">{score}%</p>
        <p className="mt-1 text-xs opacity-80">{matchLabel(score)}</p>
      </div>
    );
  }

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-lg border px-2.5 py-1 text-xs font-semibold",
        matchScoreColor(score),
      )}
    >
      <Sparkles className="h-3 w-3" />
      {score}% match con tu CV
    </span>
  );
}