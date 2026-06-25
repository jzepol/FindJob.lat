import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { Seniority } from "./types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatSalary(
  min: string | null,
  max: string | null,
  currency: string | null,
): string | null {
  if (!min && !max) return null;
  const fmt = (n: string) =>
    new Intl.NumberFormat("es-AR", { maximumFractionDigits: 0 }).format(Number(n));
  const cur = currency ?? "ARS";
  if (min && max && min !== max) return `${cur} ${fmt(min)} – ${fmt(max)}`;
  return `${cur} ${fmt(min ?? max!)}`;
}

export function timeAgo(dateStr: string | null): string {
  if (!dateStr) return "Reciente";
  const diff = Date.now() - new Date(dateStr).getTime();
  const days = Math.floor(diff / 86400000);
  if (days === 0) return "Hoy";
  if (days === 1) return "Ayer";
  if (days < 7) return `Hace ${days} días`;
  if (days < 30) return `Hace ${Math.floor(days / 7)} sem`;
  return `Hace ${Math.floor(days / 30)} mes`;
}

const SENIORITY_LABELS: Record<Seniority, string> = {
  intern: "Trainee",
  junior: "Junior",
  mid: "Semi Senior",
  senior: "Senior",
  lead: "Lead",
  director: "Director",
  unknown: "Sin nivel",
};

export function seniorityLabel(s: Seniority): string {
  return SENIORITY_LABELS[s] ?? s;
}

const MODALITY_LABELS = {
  remote: "Remoto",
  hybrid: "Híbrido",
  on_site: "Presencial",
  unknown: "A definir",
} as const;

export function modalityLabel(m: keyof typeof MODALITY_LABELS): string {
  return MODALITY_LABELS[m];
}