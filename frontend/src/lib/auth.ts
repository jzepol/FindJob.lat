import type { MatchStats } from "@/lib/types";

const DEV_TOKEN_KEY = "findjob_token";
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
const AUTH_BASE = API_BASE.replace("/api/v1", "");
const IS_DEV = process.env.NODE_ENV === "development";

export interface UserProfile {
  full_name: string | null;
  headline: string | null;
  cv_text: string | null;
  skills: string[] | null;
  preferred_locations: string[] | null;
  seniority: string | null;
}

export interface OAuthAccount {
  provider: "google";
  email: string | null;
  display_name: string | null;
  avatar_url: string | null;
}

export interface User {
  id: string;
  email: string;
  is_verified: boolean;
  karma_score: number;
  profile: UserProfile | null;
  oauth_accounts: OAuthAccount[];
}

export interface KarmaInfo {
  score: number;
  min_to_report: number;
  can_report: boolean;
  points_needed: number;
  events: Record<string, number>;
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

function authHeaders(): Record<string, string> {
  const headers: Record<string, string> = {};
  if (IS_DEV) {
    const token = getDevToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

function getDevToken(): string | null {
  if (typeof window === "undefined" || !IS_DEV) return null;
  return sessionStorage.getItem(DEV_TOKEN_KEY);
}

function setDevToken(token: string | null) {
  if (typeof window === "undefined" || !IS_DEV) return;
  if (token) sessionStorage.setItem(DEV_TOKEN_KEY, token);
  else sessionStorage.removeItem(DEV_TOKEN_KEY);
}

export function clearToken() {
  setDevToken(null);
}

export async function authFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...init?.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail));
  }
  return res.json() as Promise<T>;
}

export async function getMe(): Promise<User> {
  return authFetch<User>("/auth/me");
}

export async function login(email: string, password: string): Promise<void> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error("Credenciales inválidas");
  const data = await res.json();
  if (data.access_token) setDevToken(data.access_token);
}

export async function register(
  email: string,
  password: string,
  fullName?: string,
): Promise<void> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, full_name: fullName }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? "Error al registrarse");
  }
  const data = await res.json();
  if (data.access_token) setDevToken(data.access_token);
}

export async function exchangeOAuthCode(code: string): Promise<void> {
  const res = await fetch(`${API_BASE}/auth/oauth/exchange`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? "No se pudo completar el inicio de sesión");
  }
  const data = await res.json();
  if (data.access_token) setDevToken(data.access_token);
}

export async function logout(): Promise<void> {
  try {
    await fetch(`${API_BASE}/auth/logout`, {
      method: "POST",
      credentials: "include",
      headers: authHeaders(),
    });
  } finally {
    clearToken();
  }
}

export function googleLoginUrl(): string {
  return `${AUTH_BASE}/api/v1/auth/google/login`;
}

export async function getKarma(): Promise<KarmaInfo> {
  return authFetch<KarmaInfo>("/me/karma");
}

export async function getMatchStats(): Promise<MatchStats> {
  return authFetch<MatchStats>("/me/profile/match-stats");
}

/** Headers + credentials para requests autenticados desde el cliente. */
export function authenticatedFetchInit(): RequestInit {
  return {
    credentials: "include",
    headers: authHeaders(),
  };
}

export async function recordSearchActivity(): Promise<void> {
  try {
    await authFetch("/me/activity/search", { method: "POST" });
  } catch {
    /* ignore */
  }
}

export async function updateProfile(data: Partial<UserProfile>): Promise<UserProfile> {
  return authFetch<UserProfile>("/me/profile", {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export interface CvUploadResult {
  cv_text: string;
  chars: number;
  filename: string;
  karma_gained: number;
  karma_score: number;
  parsed_by: string;
  embedding_ready: boolean;
  summary: string | null;
  skills_extracted: string[];
  headline_extracted: string | null;
  full_name_extracted: string | null;
}

export async function uploadCv(file: File): Promise<CvUploadResult> {
  const res = await fetch(`${API_BASE}/me/profile/cv`, {
    method: "POST",
    credentials: "include",
    headers: authHeaders(),
    body: (() => {
      const form = new FormData();
      form.append("file", file);
      return form;
    })(),
  });

  if (!res.ok) {
    if (res.status === 404) {
      throw new Error(
        "El servicio de CV no está disponible en el servidor. Reiniciá la API y probá de nuevo.",
      );
    }

    const err = await res.json().catch(() => ({}));
    const detail = err.detail;
    let message = "Error al subir el CV";

    if (typeof detail === "string") {
      message = detail;
    } else if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0];
      message = typeof first === "string" ? first : (first?.msg ?? message);
    }

    throw new Error(message);
  }

  return res.json();
}

export async function submitCompanyReport(data: {
  offer_id?: string;
  company_name: string;
  report_type: string;
  description?: string;
}): Promise<void> {
  await authFetch("/company-reports", {
    method: "POST",
    body: JSON.stringify(data),
  });
}