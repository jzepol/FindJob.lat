"use client";

import { ArrowRight, FileText, Sparkles, User } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/components/auth-provider";
import { getOffersForMe } from "@/lib/auth";
import type { OfferSummary, PaginatedOffers } from "@/lib/types";
import { EmptyState } from "./empty-state";
import { OfferCard } from "./offer-card";
import { OfferCardSkeleton } from "./offer-card-skeleton";

export function ForMePageClient() {
  const { user, loading: authLoading } = useAuth();
  const hasCv = Boolean(user?.profile?.cv_text && user.profile.cv_text.length > 50);

  const [data, setData] = useState<PaginatedOffers | null>(null);
  const [items, setItems] = useState<OfferSummary[]>([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchFeed = useCallback(async (p: number, append = false) => {
    if (append) setLoadingMore(true);
    else setLoading(true);
    setError(null);
    try {
      const json = await getOffersForMe(p);
      setData(json);
      setItems((prev) => (append ? [...prev, ...json.items] : json.items));
      setPage(p);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "No pudimos cargar tus recomendaciones";
      setError(msg);
      if (!append) setItems([]);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, []);

  useEffect(() => {
    if (authLoading) return;
    if (user && hasCv) {
      fetchFeed(1);
    } else {
      setLoading(false);
    }
  }, [authLoading, user, hasCv, fetchFeed]);

  if (authLoading || loading) {
    return (
      <div className="mx-auto max-w-4xl space-y-4 px-4 py-8 sm:px-6 lg:px-8">
        {Array.from({ length: 4 }).map((_, i) => (
          <OfferCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (!user) {
    return (
      <div className="mx-auto flex min-h-[60vh] max-w-lg flex-col items-center justify-center px-4 py-16 text-center">
        <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 ring-1 ring-primary/20">
          <User className="h-8 w-8 text-primary" />
        </div>
        <h1 className="font-display text-2xl font-bold">Para vos</h1>
        <p className="mt-3 text-sm leading-relaxed text-muted">
          Iniciá sesión y subí tu CV para ver ofertas ordenadas por compatibilidad con tu perfil.
        </p>
        <Link href="/auth/login" className="btn-primary mt-8 inline-flex items-center gap-2">
          Ingresar
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    );
  }

  if (!hasCv) {
    return (
      <div className="mx-auto flex min-h-[60vh] max-w-lg flex-col items-center justify-center px-4 py-16 text-center">
        <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 ring-1 ring-primary/20">
          <FileText className="h-8 w-8 text-primary" />
        </div>
        <h1 className="font-display text-2xl font-bold">Activá Para vos</h1>
        <p className="mt-3 text-sm leading-relaxed text-muted">
          Subí tu CV en el perfil y la IA va a rankear las ofertas más compatibles con tu experiencia
          y preferencias.
        </p>
        <Link href="/perfil" className="btn-primary mt-8 inline-flex items-center gap-2">
          Subir CV
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 text-center">
        <p className="text-sm text-muted">{error}</p>
        <Link href="/perfil" className="mt-4 inline-block text-sm text-primary hover:underline">
          Revisar perfil
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-primary/25 bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
          <Sparkles className="h-3.5 w-3.5" />
          Matching con tu CV
        </div>
        <h1 className="font-display text-3xl font-bold">Para vos</h1>
        <p className="mt-2 text-muted">
          {data
            ? `${data.total.toLocaleString("es-AR")} ofertas compatibles con tu perfil`
            : "Cargando recomendaciones..."}
        </p>
        <p className="mt-1 text-xs text-muted">
          Ordenadas por similitud semántica · se aplican tus preferencias de ubicación y modalidad
        </p>
      </div>

      {items.length === 0 ? (
        <EmptyState
          title="Sin recomendaciones por ahora"
          description="Ajustá tus preferencias en el perfil o explorá todas las ofertas."
        />
      ) : (
        <div className="space-y-4">
          {items.map((offer) => (
            <OfferCard key={offer.id} offer={offer} showMatchScore />
          ))}
          {data && page < data.pages && (
            <button
              type="button"
              disabled={loadingMore}
              onClick={() => fetchFeed(page + 1, true)}
              className="w-full rounded-2xl border border-primary/30 bg-primary/10 py-3 text-sm font-medium text-primary transition hover:bg-primary/20 disabled:opacity-50"
            >
              {loadingMore ? "Cargando..." : "Cargar más recomendaciones"}
            </button>
          )}
        </div>
      )}

      <p className="mt-8 text-center text-sm text-muted">
        ¿Querés buscar con filtros?{" "}
        <Link href="/jobs" className="text-primary hover:underline">
          Ir a todas las ofertas
        </Link>
      </p>
    </div>
  );
}