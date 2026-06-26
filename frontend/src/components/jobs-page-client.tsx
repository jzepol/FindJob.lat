"use client";

import { Sparkles } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useAuth } from "@/components/auth-provider";
import { authenticatedFetchInit, recordSearchActivity } from "@/lib/auth";
import type { Modality, OfferSummary, PaginatedOffers, Seniority } from "@/lib/types";
import { EmptyState } from "./empty-state";
import { FiltersSidebar, type FilterState } from "./filters-sidebar";
import { OfferCard } from "./offer-card";
import { OfferCardSkeleton } from "./offer-card-skeleton";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

function parseFilters(params: URLSearchParams, hasCv: boolean): FilterState {
  const modality = params.getAll("modality") as Modality[];
  const seniority = params.getAll("seniority") as Seniority[];
  const sortParam = params.get("sort") as FilterState["sort"] | null;
  return {
    q: params.get("q") ?? "",
    location: params.get("location") ?? "",
    modality: modality.length ? modality : params.get("modality") ? [params.get("modality") as Modality] : [],
    seniority: seniority.length ? seniority : params.get("seniority") ? [params.get("seniority") as Seniority] : [],
    source: params.get("source") ?? "",
    sources: params.getAll("sources").length
      ? params.getAll("sources")
      : params.get("source")
        ? [params.get("source")!]
        : [],
    salary_min: Number(params.get("salary_min") ?? 0),
    published_within: (params.get("published_within") as FilterState["published_within"]) ?? "",
    sort: sortParam ?? (hasCv ? "relevance" : "published_at"),
  };
}

function buildQuery(filters: FilterState, page: number): string {
  const p = new URLSearchParams();
  if (filters.q) p.set("q", filters.q);
  if (filters.location) p.set("location", filters.location);
  filters.sources.forEach((s) => p.append("sources", s));
  if (filters.salary_min > 0) p.set("salary_min", String(filters.salary_min));
  if (filters.published_within) p.set("published_within", filters.published_within);
  p.set("sort", filters.sort);
  p.set("page", String(page));
  p.set("page_size", "20");
  filters.modality.forEach((m) => p.append("modality", m));
  filters.seniority.forEach((s) => p.append("seniority", s));
  return p.toString();
}

export function JobsPageClient({ sources }: { sources: { slug: string; name: string }[] }) {
  const searchParams = useSearchParams();
  const { user } = useAuth();
  const hasCv = Boolean(user?.profile?.cv_text && user.profile.cv_text.length > 50);

  const [filters, setFilters] = useState<FilterState>(() =>
    parseFilters(searchParams, hasCv),
  );
  const [data, setData] = useState<PaginatedOffers | null>(null);
  const [items, setItems] = useState<OfferSummary[]>([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);

  const fetchOffers = useCallback(
    async (f: FilterState, p: number, append = false) => {
      if (append) setLoadingMore(true);
      else setLoading(true);
      try {
        const res = await fetch(`${API_BASE}/offers?${buildQuery(f, p)}`, authenticatedFetchInit());
        const json: PaginatedOffers = await res.json();
        setData(json);
        setItems((prev) => (append ? [...prev, ...json.items] : json.items));
        setPage(p);
      } catch {
        if (!append) setItems([]);
      } finally {
        setLoading(false);
        setLoadingMore(false);
      }
    },
    [],
  );

  useEffect(() => {
    setFilters(parseFilters(searchParams, hasCv));
  }, [searchParams, hasCv]);

  useEffect(() => {
    const params = buildQuery(filters, 1);
    window.history.replaceState(null, "", `/jobs?${params}`);
    const t = setTimeout(() => {
      fetchOffers(filters, 1);
      if (filters.q || filters.location || filters.modality.length) {
        recordSearchActivity();
      }
    }, 300);
    return () => clearTimeout(t);
  }, [filters, fetchOffers]);

  const cvMatchingActive = data?.matching_mode === "cv" && filters.sort === "relevance";

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="font-display text-3xl font-bold">Buscar empleos</h1>
        <p className="mt-1 text-muted">
          {data ? `${data.total.toLocaleString("es-AR")} ofertas encontradas` : "Buscando..."}
        </p>
      </div>

      {cvMatchingActive && (
        <div className="mb-6 flex flex-wrap items-center gap-3 rounded-2xl border border-primary/25 bg-primary/10 px-4 py-3 text-sm">
          <Sparkles className="h-4 w-4 shrink-0 text-primary" />
          <span className="text-foreground-secondary">
            Ordenando por compatibilidad con tu CV usando IA semántica.
          </span>
          <Link href="/perfil" className="text-primary hover:underline">
            Ver perfil
          </Link>
        </div>
      )}

      {!hasCv && filters.sort === "relevance" && (
        <div className="mb-6 rounded-2xl border border-border bg-surface-2/60 px-4 py-3 text-sm text-muted">
          <Link href="/auth/login" className="text-primary hover:underline">
            Iniciá sesión
          </Link>{" "}
          y subí tu CV para activar el orden por relevancia IA.
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        <FiltersSidebar
          filters={filters}
          onChange={setFilters}
          sources={sources}
          cvMatchingAvailable={hasCv}
          className="lg:sticky lg:top-24 lg:self-start"
        />

        <div className="space-y-4">
          {loading ? (
            Array.from({ length: 4 }).map((_, i) => <OfferCardSkeleton key={i} />)
          ) : items.length === 0 ? (
            <EmptyState />
          ) : (
            <>
              {items.map((offer) => (
                <OfferCard key={offer.id} offer={offer} showMatchScore={cvMatchingActive} />
              ))}
              {data && page < data.pages && (
                <button
                  type="button"
                  disabled={loadingMore}
                  onClick={() => fetchOffers(filters, page + 1, true)}
                  className="w-full rounded-2xl border border-primary/30 bg-primary/10 py-3 text-sm font-medium text-primary transition hover:bg-primary/20 disabled:opacity-50"
                >
                  {loadingMore ? "Cargando..." : "Cargar más ofertas"}
                </button>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}