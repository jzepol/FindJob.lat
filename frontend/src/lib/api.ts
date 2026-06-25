import type {
  OfferDetail,
  OfferSummary,
  PaginatedOffers,
  SalaryRole,
  SearchFilters,
  Source,
  Stats,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

function buildParams(filters: SearchFilters & { page_size?: number }): string {
  const params = new URLSearchParams();
  if (filters.q) params.set("q", filters.q);
  if (filters.location) params.set("location", filters.location);
  if (filters.source) params.set("source", filters.source);
  if (filters.salary_min) params.set("salary_min", String(filters.salary_min));
  if (filters.published_within) params.set("published_within", filters.published_within);
  if (filters.sort) params.set("sort", filters.sort);
  if (filters.page) params.set("page", String(filters.page));
  if (filters.page_size) params.set("page_size", String(filters.page_size));
  filters.modality?.forEach((m) => params.append("modality", m));
  filters.seniority?.forEach((s) => params.append("seniority", s));
  return params.toString();
}

async function fetchApi<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    next: { revalidate: 60 },
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${path}`);
  }
  return res.json() as Promise<T>;
}

export async function getOffers(filters: SearchFilters = {}): Promise<PaginatedOffers> {
  const qs = buildParams({ page_size: 20, ...filters });
  return fetchApi<PaginatedOffers>(`/offers?${qs}`);
}

export async function getFeaturedOffers(limit = 6): Promise<OfferSummary[]> {
  return fetchApi<OfferSummary[]>(`/offers/featured?limit=${limit}`);
}

export async function getOffer(id: string): Promise<OfferDetail> {
  return fetchApi<OfferDetail>(`/offers/${id}`, { cache: "no-store" });
}

export async function getSimilarOffers(id: string): Promise<OfferSummary[]> {
  return fetchApi<OfferSummary[]>(`/offers/${id}/similar?limit=4`);
}

export async function getStats(): Promise<Stats> {
  return fetchApi<Stats>("/stats");
}

export async function getSources(): Promise<Source[]> {
  return fetchApi<Source[]>("/sources");
}

export async function getSalaries(params?: {
  seniority?: string;
  location?: string;
}): Promise<SalaryRole[]> {
  const qs = new URLSearchParams();
  if (params?.seniority) qs.set("seniority", params.seniority);
  if (params?.location) qs.set("location", params.location);
  const query = qs.toString();
  return fetchApi<SalaryRole[]>(`/salaries${query ? `?${query}` : ""}`);
}