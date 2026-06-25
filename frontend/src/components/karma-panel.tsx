"use client";

import { AlertTriangle, Search, Shield, Sparkles, Star, UserCheck } from "lucide-react";
import type { KarmaInfo } from "@/lib/auth";
import { cn } from "@/lib/utils";

const KARMA_WAYS = [
  { key: "oauth_linked", label: "Ingresar con Google", points: 15, icon: UserCheck },
  { key: "email_verified", label: "Registro con email", points: 15, icon: UserCheck },
  { key: "profile_complete", label: "Completar perfil", points: 20, icon: Sparkles },
  { key: "cv_uploaded", label: "Subir CV", points: 25, icon: Shield },
  { key: "first_search", label: "Primera búsqueda", points: 10, icon: Search },
] as const;

export function KarmaPanel({ karma }: { karma: KarmaInfo }) {
  const progress = Math.min(100, (karma.score / karma.min_to_report) * 100);
  const earnedKeys = new Set(Object.keys(karma.events ?? {}));

  return (
    <div className="card-premium overflow-hidden rounded-2xl">
      <div className="border-b border-border bg-gradient-to-r from-primary/10 via-transparent to-secondary/10 px-5 py-4 sm:px-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/15 ring-1 ring-primary/25">
              <Star className="h-5 w-5 fill-primary text-primary" />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-primary">
                Karma de la comunidad
              </p>
              <p className="mt-0.5 text-sm text-foreground-secondary">
                Reputación que desbloquea funciones
              </p>
            </div>
          </div>
          <div className="text-right">
            <p className="font-mono text-3xl font-bold tracking-tight text-foreground">
              {karma.score}
            </p>
            <p className="text-xs text-muted">/ {karma.min_to_report} pts</p>
          </div>
        </div>
      </div>

      <div className="space-y-5 px-5 py-5 sm:px-6">
        <div>
          <div className="mb-2 flex items-center justify-between text-sm">
            <span className="font-medium text-foreground">
              {karma.can_report ? "Nivel desbloqueado" : "Progreso hacia reportar empresas"}
            </span>
            <span className="font-mono text-xs text-muted">{Math.round(progress)}%</span>
          </div>
          <div className="h-2.5 overflow-hidden rounded-full bg-surface-2 ring-1 ring-border">
            <div
              className={cn(
                "h-full rounded-full transition-all duration-700",
                karma.can_report
                  ? "bg-gradient-to-r from-primary to-secondary"
                  : "bg-gradient-to-r from-primary/80 to-primary",
              )}
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="mt-2.5 text-xs leading-relaxed text-muted">
            {karma.can_report ? (
              <span className="inline-flex items-center gap-1.5 text-primary">
                <Shield className="h-3.5 w-3.5" />
                Podés reportar empresas y ayudar a validar ofertas en la comunidad.
              </span>
            ) : (
              <>
                <AlertTriangle className="mr-1 inline h-3.5 w-3.5 text-warning" />
                Te faltan <strong className="text-foreground">{karma.points_needed} puntos</strong>{" "}
                para reportar empresas sospechosas. Completá tu perfil y explorá ofertas.
              </>
            )}
          </p>
        </div>

        <div className="rounded-xl border border-border bg-surface-2/50 p-4">
          <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted">
            Cómo sumar karma
          </p>
          <ul className="space-y-2">
            {KARMA_WAYS.map((way) => {
              const done = earnedKeys.has(way.key);
              return (
                <li
                  key={way.key}
                  className={cn(
                    "flex items-center justify-between rounded-lg px-2 py-1.5 text-sm transition",
                    done && "bg-primary/5",
                  )}
                >
                  <span className="flex items-center gap-2 text-foreground-secondary">
                    <way.icon
                      className={cn("h-3.5 w-3.5", done ? "text-primary" : "text-muted")}
                    />
                    <span className={done ? "text-foreground" : ""}>{way.label}</span>
                  </span>
                  <span
                    className={cn(
                      "font-mono text-xs font-semibold",
                      done ? "text-primary" : "text-muted",
                    )}
                  >
                    {done ? "✓" : "+"}
                    {way.points}
                  </span>
                </li>
              );
            })}
          </ul>
        </div>
      </div>
    </div>
  );
}