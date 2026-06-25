const TOKEN_KEY = "findjob_token";
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
const AUTH_BASE = API_BASE.replace("/api/v1", "");

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

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export async function authFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
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

export async function login(email: string, password: string): Promise<string> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error("Credenciales inválidas");
  const data = await res.json();
  setToken(data.access_token);
  return data.access_token;
}

export async function register(
  email: string,
  password: string,
  fullName?: string,
): Promise<string> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, full_name: fullName }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? "Error al registrarse");
  }
  const data = await res.json();
  setToken(data.access_token);
  return data.access_token;
}

export function googleLoginUrl(): string {
  return `${AUTH_BASE}/api/v1/auth/google/login`;
}

export async function getKarma(): Promise<KarmaInfo> {
  return authFetch<KarmaInfo>("/me/karma");
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