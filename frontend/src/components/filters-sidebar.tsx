"use client";

import { SlidersHorizontal } from "lucide-react";
import type { Modality, Seniority } from "@/lib/types";
import { cn } from "@/lib/utils";

export interface FilterState {
  q: string;
  location: string;
  modality: Modality[];
  seniority: Seniority[];
  source: string;
  salary_min: number;
  published_within: "" | "today" | "week" | "month";
  sort: "relevance" | "published_at" | "salary";
}

interface FiltersSidebarProps {
  filters: FilterState;
  onChange: (filters: FilterState) => void;
  sources: { slug: string; name: string }[];
  className?: string;
}

export function FiltersSidebar({
  filters,
  onChange,
  sources,
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
          <label className="mb-1.5 block text-xs font-medium text-muted">Fuente</label>
          <select
            value={filters.source}
            onChange={(e) => update("source", e.target.value)}
            className="w-full rounded-xl bg-surface-2 px-3 py-2 text-sm outline-none"
          >
            <option value="">Todas</option>
            {sources.map((s) => (
              <option key={s.slug} value={s.slug}>
                {s.name}
              </option>
            ))}
          </select>
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
            <option value="relevance">Relevancia IA</option>
            <option value="published_at">Más recientes</option>
            <option value="salary">Mayor salario</option>
          </select>
        </div>
      </div>
    </aside>
  );
}