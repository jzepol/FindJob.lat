import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { HeroSection } from "@/components/hero-section";
import { OfferCard } from "@/components/offer-card";
import { PortalsSection } from "@/components/portals-section";
import { StatsSection } from "@/components/stats-section";
import { getFeaturedOffers, getStats } from "@/lib/api";
import type { OfferSummary, Stats } from "@/lib/types";

export default async function HomePage() {
  let featured: OfferSummary[] = [];
  let stats: Stats = { active_offers: 0, companies: 0, sources: 3, with_salary: 0 };

  try {
    [featured, stats] = await Promise.all([getFeaturedOffers(6), getStats()]);
  } catch {
    // API offline — página igual renderiza
  }

  return (
    <>
      <HeroSection stats={stats} />

      <PortalsSection />

      {stats.active_offers > 0 && <StatsSection stats={stats} />}

      <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
        <div className="mb-10 flex items-end justify-between">
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-primary">
              Destacadas
            </p>
            <h2 className="font-display text-2xl font-bold tracking-tight sm:text-3xl">
              Ofertas recientes
            </h2>
            <p className="mt-2 text-sm text-muted">
              Curadas de los mejores portales con descripción completa
            </p>
          </div>
          <Link
            href="/jobs"
            className="hidden items-center gap-1.5 rounded-xl border border-border px-4 py-2 text-sm font-medium text-foreground-secondary transition hover:border-primary/30 hover:text-primary sm:flex"
          >
            Ver todas
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>

        {featured.length > 0 ? (
          <div className="grid gap-5 lg:grid-cols-2">
            {featured.map((offer) => (
              <OfferCard key={offer.id} offer={offer} />
            ))}
          </div>
        ) : (
          <div className="card-premium rounded-2xl p-12 text-center">
            <p className="text-foreground-secondary">Iniciá el backend para ver ofertas en vivo.</p>
            <code className="mt-3 inline-block rounded-lg bg-surface-2 px-3 py-1.5 font-mono text-xs text-muted">
              uvicorn app.main:app --reload
            </code>
          </div>
        )}

        <div className="mt-8 text-center sm:hidden">
          <Link
            href="/jobs"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-primary"
          >
            Ver todas las ofertas <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>
    </>
  );
}