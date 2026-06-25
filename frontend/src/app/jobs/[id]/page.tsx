import Link from "next/link";
import { notFound } from "next/navigation";
import {
  ArrowLeft,
  Bookmark,
  Building2,
  ExternalLink,
  Layers,
  MapPin,
  Share2,
  Sparkles,
} from "lucide-react";
import { OfferCard } from "@/components/offer-card";
import { ModalityBadge } from "@/components/modality-badge";
import { SeniorityBadge } from "@/components/seniority-badge";
import { CompanyAvatar } from "@/components/company-avatar";
import { CompanyWarningBanner } from "@/components/company-warning";
import { ReportCompanyButton } from "@/components/report-company-modal";
import { getOffer, getSimilarOffers } from "@/lib/api";
import { formatSalary, timeAgo } from "@/lib/utils";

export default async function JobDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  let offer;
  let similar = [];

  try {
    offer = await getOffer(id);
    similar = await getSimilarOffers(id);
  } catch {
    notFound();
  }

  const salary = formatSalary(offer.salary_min, offer.salary_max, offer.salary_currency);

  return (
    <div>
      <div
        className="border-b border-border px-4 py-10 sm:px-6 lg:px-8"
        style={{
          background:
            "linear-gradient(180deg, rgba(20,184,166,0.08) 0%, transparent 100%)",
        }}
      >
        <div className="mx-auto max-w-7xl">
          <Link
            href="/jobs"
            className="mb-6 inline-flex items-center gap-1 text-sm text-muted hover:text-primary"
          >
            <ArrowLeft className="h-4 w-4" /> Volver a búsqueda
          </Link>

          {offer.company_warning && (
            <CompanyWarningBanner warning={offer.company_warning} className="mb-6" />
          )}

          <div className="grid gap-8 lg:grid-cols-[1fr_320px]">
            <div>
              <div className="flex gap-4">
                <CompanyAvatar company={offer.company} className="h-16 w-16 text-2xl" />
                <div>
                  <h1 className="font-display text-3xl font-bold leading-tight sm:text-4xl">
                    {offer.title}
                  </h1>
                  <div className="mt-3 flex flex-wrap items-center gap-3 text-muted">
                    <span className="inline-flex items-center gap-1">
                      <Building2 className="h-4 w-4" /> {offer.company}
                    </span>
                    {offer.location && (
                      <span className="inline-flex items-center gap-1">
                        <MapPin className="h-4 w-4" /> {offer.location}
                      </span>
                    )}
                    <span>{timeAgo(offer.published_at)}</span>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <ModalityBadge modality={offer.modality} />
                    <SeniorityBadge seniority={offer.seniority} />
                  </div>
                </div>
              </div>
            </div>

            <aside className="glass h-fit rounded-2xl p-5 lg:sticky lg:top-24">
              {salary && (
                <p className="font-mono text-2xl font-bold text-accent">{salary}</p>
              )}
              <div className="mt-4 space-y-2">
                <a
                  href={offer.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex w-full items-center justify-center gap-2 rounded-xl bg-primary py-3 text-sm font-semibold text-white transition hover:bg-primary-hover"
                >
                  Aplicar <ExternalLink className="h-4 w-4" />
                </a>
                <button
                  type="button"
                  className="flex w-full items-center justify-center gap-2 rounded-xl border border-border py-2.5 text-sm transition hover:border-primary/40"
                >
                  <Bookmark className="h-4 w-4" /> Guardar
                </button>
                <button
                  type="button"
                  className="flex w-full items-center justify-center gap-2 rounded-xl border border-border py-2.5 text-sm transition hover:border-primary/40"
                >
                  <Share2 className="h-4 w-4" /> Compartir
                </button>
                <ReportCompanyButton offerId={offer.id} companyName={offer.company} />
              </div>

              {offer.duplicate_count > 1 && (
                <div className="mt-5 border-t border-border pt-5">
                  <p className="mb-3 flex items-center gap-1.5 text-xs font-medium text-secondary">
                    <Layers className="h-3.5 w-3.5" />
                    También en {offer.duplicate_count} portales
                  </p>
                  <div className="space-y-2">
                    {offer.duplicates.map((dup) => (
                      <a
                        key={dup.id}
                        href={dup.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center justify-between rounded-lg bg-surface-2 px-3 py-2 text-xs transition hover:bg-surface-2"
                      >
                        {dup.source.name}
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </aside>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="max-w-3xl">
          <h2 className="font-display text-xl font-bold">Descripción</h2>
          {offer.description ? (
            <div className="mt-4 max-w-none whitespace-pre-wrap text-sm leading-relaxed text-foreground-secondary">
              {offer.description}
            </div>
          ) : (
            <p className="mt-4 text-muted">Sin descripción disponible.</p>
          )}
        </div>

        {similar.length > 0 && (
          <section className="mt-16">
            <div className="mb-6 flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              <h2 className="font-display text-xl font-bold">Ofertas similares</h2>
              {offer.has_embedding && (
                <span className="text-xs text-muted">· recomendadas por IA</span>
              )}
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              {similar.map((o) => (
                <OfferCard key={o.id} offer={o} />
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}