"use client";

import Link from "next/link";
import { ArrowUpRight, Bookmark, Building2, Clock, Layers, MapPin } from "lucide-react";
import type { OfferSummary } from "@/lib/types";
import { cn, formatSalary, timeAgo } from "@/lib/utils";
import { CompanyAvatar } from "./company-avatar";
import { MatchScoreCorner } from "./match-score-corner";
import { ModalityBadge } from "./modality-badge";
import { SeniorityBadge } from "./seniority-badge";
import { SourceBadge } from "./source-badge";
import { useToast } from "./toast-provider";

export function OfferCard({
  offer,
  className,
  showMatchScore = false,
}: {
  offer: OfferSummary;
  className?: string;
  showMatchScore?: boolean;
}) {
  const toast = useToast();
  const salary = formatSalary(offer.salary_min, offer.salary_max, offer.salary_currency);

  return (
    <article
      className={cn(
        "card-premium group relative overflow-hidden rounded-2xl",
        className,
      )}
    >
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/40 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />

      {showMatchScore && offer.match_score != null && (
        <MatchScoreCorner score={offer.match_score} />
      )}

      <div
        className={cn(
          "flex flex-col gap-5 p-5 sm:p-6",
          showMatchScore && offer.match_score != null && "pr-24 sm:pr-28",
        )}
      >
        <div className="flex items-start gap-4">
          <CompanyAvatar company={offer.company} size="lg" />

          <div className="min-w-0 flex-1">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <Link href={`/jobs/${offer.id}`}>
                  <h3 className="font-display text-lg font-bold leading-snug tracking-tight transition-colors group-hover:text-primary sm:text-xl">
                    {offer.title}
                  </h3>
                </Link>
                <p className="mt-1 flex items-center gap-1.5 text-sm text-foreground-secondary">
                  <Building2 className="h-3.5 w-3.5 shrink-0 text-muted" />
                  <span className="truncate font-medium">{offer.company}</span>
                </p>
              </div>

              <button
                type="button"
                onClick={() => toast("Oferta guardada")}
                className="shrink-0 rounded-xl border border-border p-2 text-muted opacity-0 transition-all hover:border-primary/30 hover:bg-primary/5 hover:text-primary group-hover:opacity-100"
                aria-label="Guardar oferta"
              >
                <Bookmark className="h-4 w-4" />
              </button>
            </div>

            {offer.location && (
              <p className="mt-2 flex items-center gap-1.5 text-sm text-muted">
                <MapPin className="h-3.5 w-3.5 shrink-0" />
                {offer.location}
              </p>
            )}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <ModalityBadge modality={offer.modality} />
          <SeniorityBadge seniority={offer.seniority} />
          {offer.duplicate_count > 1 && (
            <span className="inline-flex items-center gap-1 rounded-lg border border-secondary/25 bg-secondary/10 px-2.5 py-1 text-xs font-medium text-secondary">
              <Layers className="h-3 w-3" />
              {offer.duplicate_count} portales
            </span>
          )}
        </div>

        <div className="flex flex-wrap items-end justify-between gap-4 border-t border-border pt-4">
          <div className="space-y-2">
            {salary ? (
              <p className="font-mono text-base font-semibold tracking-tight text-foreground">
                {salary}
                <span className="ml-1.5 text-xs font-normal text-muted">/mes est.</span>
              </p>
            ) : (
              <p className="text-sm text-muted">Salario no informado</p>
            )}
            <div className="flex flex-wrap items-center gap-3 text-xs text-muted">
              <SourceBadge source={offer.source} />
              <span className="inline-flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {timeAgo(offer.published_at)}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Link
              href={`/jobs/${offer.id}`}
              className="rounded-xl border border-border px-4 py-2.5 text-sm font-medium text-foreground-secondary transition hover:border-primary/30 hover:text-primary"
            >
              Detalle
            </Link>
            <a
              href={offer.url}
              target="_blank"
              rel="noopener noreferrer"
              className="group/btn inline-flex items-center gap-1.5 rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-white transition-all hover:bg-primary-hover active:scale-[0.98]"
            >
              Aplicar
              <ArrowUpRight className="h-3.5 w-3.5 transition-transform group-hover/btn:translate-x-0.5 group-hover/btn:-translate-y-0.5" />
            </a>
          </div>
        </div>
      </div>
    </article>
  );
}