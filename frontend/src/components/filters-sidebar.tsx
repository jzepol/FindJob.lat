"use client";

import { SlidersHorizontal } from "lucide-react";
import type { Modality, Seniority } from "@/lib/types";
import { cn } from "@/lib/utils";

export interface FilterState {
  q: string;
  location: string;
  modality: Modality[];
  seniority: Seniority[];
  /** @deprecated use sources */
  source: string;
  sources: string[];
  salary_min: number;
  published_within: "" | "today" | "week" | "month";
  sort: "relevance" | "published_at" | "salary";
}

interface FiltersSidebarProps {
  filters: FilterState;
  onChange: (filters: FilterState) => void;
  sources: { slug: string; name: string }[];
  cvMatchingAvailable?: boolean;
  className?: string;
}

export function FiltersSidebar({
  filters,
  onChange,
  sources,
  cvMatchingAvailable = false,
  className,
}: FiltersSidebarProps) {
  function update<K extends keyof FilterState>(key: K, value: FilterState[K]) {
    onChange({ ...filters, [key]: value });
  }

  function toggleModality(m: Modality) {
    const next = filters.modality.includes(m)
      ? filters.modality.filter((x) => x !== m)
      : [...filters.modality, m];
    update("modality", next);
  }

  function toggleSeniority(s: Seniority) {
    const next = filters.seniority.includes(s)
      ? filters.seniority.filter((x) => x !== s)
      : [...filters.seniority, s];
    update("seniority", next);
  }

  function toggleSource(slug: string) {
    const next = filters.sources.includes(slug)
      ? filters.sources.filter((x) => x !== slug)
      : [...filters.sources, slug];
    onChange({ ...filters, sources: next, source: "" });
  }

  return (
    <aside className={cn("glass rounded-2xl p-5", className)}>
      <div className="mb-5 flex items-center gap-2">
        <SlidersHorizontal className="h-4 w-4 text-primary" />
        <h2 className="font-display font-semibold">Filtros</h2>
      </div>

      <div className="space-y-5">
        <div>
          <label className="mb-1.5 block text-xs font-medium text-muted">Keywords</label>
          <input
            value={filters.q}
            onChange={(e) => update("q", e.target.value)}
            className="w-full rounded-xl bg-surface-2 px-3 py-2 text-sm outline-none ring-primary/50 focus:ring-2"
            placeholder="python, react..."
          />
        </div>

        <div>
          <label className="mb-1.5 block text-xs font-medium text-muted">Ubicación</label>
          <input
            value={filters.location}
            onChange={(e) => update("location", e.target.value)}
            className="w-full rounded-xl bg-surface-2 px-3 py-2 text-sm outline-none ring-primary/50 focus:ring-2"
            placeholder="Buenos Aires"
          />
        </div>

        <div>
          <label className="mb-2 block text-xs font-medium text-muted">Modalidad</label>
          <div className="flex flex-wrap gap-2">
            {(["remote", "hybrid", "on_site"] as Modality[]).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => toggleModality(m)}
                className={cn(
                  "rounded-full border px-3 py-1 text-xs transition",
                  filters.modality.includes(m)
                    ? "border-primary bg-primary/15 text-primary"
                    : "border-border text-muted hover:border-foreground-secondary/40",
                )}
              >
                {m === "remote" ? "Remoto" : m === "hybrid" ? "Híbrido" : "Presencial"}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="mb-2 block text-xs font-medium text-muted">Seniority</label>
          <div className="flex flex-wrap gap-2">
            {(["junior", "mid", "senior", "lead"] as Seniority[]).map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => toggleSeniority(s)}
                className={cn(
                  "rounded-full border px-3 py-1 text-xs capitalize transition",
                  filters.seniority.includes(s)
                    ? "border-secondary bg-secondary/15 text-secondary"
                    : "border-border text-muted hover:border-foreground-secondary/40",
                )}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="mb-1.5 block text-xs font-medium text-muted">
            Salario mínimo ({filters.salary_min.toLocaleString("es-AR")})
          </label>
          <input
            type="range"
            min={0}
            max={5000000}
            step={100000}
            value={filters.salary_min}
            onChange={(e) => update("salary_min", Number(e.target.value))}
            className="w-full accent-primary"
          />
        </div>

        <div>
          <label className="mb-2 block text-xs font-medium text-muted">
            Portales {filters.sources.length > 0 && `(${filters.sources.length})`}
          </label>
          <div className="flex flex-col gap-1.5">
            {sources.map((s) => (
              <label
                key={s.slug}
                className="flex cursor-pointer items-center gap-2 rounded-lg px-2 py-1.5 text-sm transition hover:bg-surface-2"
              >
                <input
                  type="checkbox"
                  checked={filters.sources.includes(s.slug)}
                  onChange={() => toggleSource(s.slug)}
                  className="accent-primary"
                />
                <span className="text-foreground-secondary">{s.name}</span>
              </label>
            ))}
          </div>
          {filters.sources.length > 0 && (
            <button
              type="button"
              onClick={() => onChange({ ...filters, sources: [], source: "" })}
              className="mt-2 text-xs text-primary hover:underline"
            >
              Limpiar portales
            </button>
          )}
        </div>

        <div>
          <label className="mb-1.5 block text-xs font-medium text-muted">Publicado</label>
          <select
            value={filters.published_within}
            onChange={(e) =>
              update("published_within", e.target.value as FilterState["published_within"])
            }
            className="w-full rounded-xl bg-surface-2 px-3 py-2 text-sm outline-none"
          >
            <option value="">Cualquier fecha</option>
            <option value="today">Hoy</option>
            <option value="week">Esta semana</option>
            <option value="month">Este mes</option>
          </select>
        </div>

        <div>
          <label className="mb-1.5 block text-xs font-medium text-muted">Ordenar</label>
          <select
            value={filters.sort}
            onChange={(e) => update("sort", e.target.value as FilterState["sort"])}
            className="w-full rounded-xl bg-surface-2 px-3 py-2 text-sm outline-none"
          >
            <option value="relevance">
              {cvMatchingAvailable ? "Relevancia IA (tu CV)" : "Relevancia IA"}
            </option>
            <option value="published_at">Más recientes</option>
            <option value="salary">Mayor salario</option>
          </select>
        </div>
      </div>
    </aside>
  );
}