export type Modality = "remote" | "hybrid" | "on_site" | "unknown";
export type JobType =
  | "full_time"
  | "part_time"
  | "contract"
  | "freelance"
  | "internship"
  | "temporary"
  | "unknown";
export type Seniority =
  | "intern"
  | "junior"
  | "mid"
  | "senior"
  | "lead"
  | "director"
  | "unknown";

export interface Source {
  id: string;
  slug: string;
  name: string;
  base_url: string;
}

export interface CompanyWarning {
  company: string;
  normalized_company: string;
  verified_reports: number;
  primary_issue: string;
  breakdown: Record<string, number>;
  severity: string;
  message: string;
}

export interface OfferSummary {
  id: string;
  title: string;
  company: string;
  location: string | null;
  modality: Modality;
  job_type: JobType;
  seniority: Seniority;
  status: string;
  salary_min: string | null;
  salary_max: string | null;
  salary_currency: string | null;
  url: string;
  published_at: string | null;
  source: Source;
  created_at: string;
  updated_at: string;
  duplicate_count: number;
  company_warning?: CompanyWarning | null;
  match_score?: number | null;
}

export interface OfferDetail extends OfferSummary {
  normalized_title: string | null;
  normalized_company: string | null;
  description: string | null;
  external_id: string;
  has_embedding: boolean;
  duplicates: OfferSummary[];
}

export interface PaginatedOffers {
  items: OfferSummary[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
  matching_mode?: "cv" | null;
}

export interface MatchStats {
  embedding_ready: boolean;
  match_score: number | null;
  strong_matches: number;
  offers_analyzed: number;
}

export interface Stats {
  active_offers: number;
  companies: number;
  sources: number;
  with_salary: number;
}

export interface SalaryRole {
  role: string;
  seniority: Seniority;
  count: number;
  salary_min: string | null;
  salary_max: string | null;
  salary_avg: string | null;
  currency: string | null;
}

export interface SearchFilters {
  q?: string;
  location?: string;
  modality?: Modality[];
  seniority?: Seniority[];
  source?: string;
  salary_min?: number;
  published_within?: "today" | "week" | "month";
  sort?: "relevance" | "published_at" | "salary";
  page?: number;
}