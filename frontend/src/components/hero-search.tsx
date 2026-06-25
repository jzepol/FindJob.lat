"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { ArrowRight, MapPin, Search, SlidersHorizontal } from "lucide-react";
import type { Modality, Seniority } from "@/lib/types";
import { cn } from "@/lib/utils";

export function HeroSearch() {
  const router = useRouter();
  const [q, setQ] = useState("");
  const [location, setLocation] = useState("");
  const [modality, setModality] = useState<Modality | "">("");
  const [seniority, setSeniority] = useState<Seniority | "">("");
  const [showFilters, setShowFilters] = useState(false);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (location) params.set("location", location);
    if (modality) params.set("modality", modality);
    if (seniority) params.set("seniority", seniority);
    router.push(`/jobs?${params.toString()}`);
  }

  return (
    <form onSubmit={handleSearch} className="search-premium mx-auto max-w-3xl rounded-2xl p-1.5 sm:p-2">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 h-[18px] w-[18px] -translate-y-1/2 text-muted" />
          <input
            type="text"
            placeholder="Puesto, skill o empresa..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
            className="w-full rounded-xl bg-surface-2/60 py-4 pl-12 pr-4 text-[15px] text-foreground outline-none transition placeholder:text-muted focus:bg-surface-2"
          />
        </div>
        <button
          type="submit"
          className="group flex items-center justify-center gap-2 rounded-xl bg-primary px-7 py-4 text-[15px] font-semibold text-white transition-all hover:bg-primary-hover active:scale-[0.98] sm:shrink-0"
        >
          Buscar empleos
          <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
        </button>
      </div>

      <div className="mt-1.5 flex items-center justify-between px-2 pb-1 pt-2">
        <button
          type="button"
          onClick={() => setShowFilters(!showFilters)}
          className={cn(
            "inline-flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs font-medium transition",
            showFilters ? "text-primary" : "text-muted hover:text-foreground",
          )}
        >
          <SlidersHorizontal className="h-3.5 w-3.5" />
          Filtros avanzados
        </button>
        <span className="text-xs text-muted">Gratis · Sin registro</span>
      </div>

      {showFilters && (
        <div className="mt-1 flex flex-col gap-2 border-t border-border px-1 pb-1 pt-3 sm:flex-row">
          <div className="relative flex-1">
            <MapPin className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted" />
            <input
              type="text"
              placeholder="Ciudad o provincia"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full rounded-xl border border-border bg-surface-2/50 py-2.5 pl-9 pr-3 text-sm outline-none transition placeholder:text-muted focus:border-primary/30"
            />
          </div>
          <select
            value={modality}
            onChange={(e) => setModality(e.target.value as Modality | "")}
            className="rounded-xl border border-border bg-surface-2/50 px-3 py-2.5 text-sm outline-none transition focus:border-primary/30"
          >
            <option value="">Modalidad</option>
            <option value="remote">Remoto</option>
            <option value="hybrid">Híbrido</option>
            <option value="on_site">Presencial</option>
          </select>
          <select
            value={seniority}
            onChange={(e) => setSeniority(e.target.value as Seniority | "")}
            className="rounded-xl border border-border bg-surface-2/50 px-3 py-2.5 text-sm outline-none transition focus:border-primary/30"
          >
            <option value="">Seniority</option>
            <option value="junior">Junior</option>
            <option value="mid">Semi Senior</option>
            <option value="senior">Senior</option>
            <option value="lead">Lead</option>
          </select>
        </div>
      )}
    </form>
  );
}