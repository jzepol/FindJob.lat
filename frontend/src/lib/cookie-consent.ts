export const CONSENT_VERSION = 1;
export const CONSENT_STORAGE_KEY = "findjob_cookie_consent";

export interface CookieConsent {
  version: number;
  updatedAt: string;
  /** Siempre activas: sesión, seguridad, tema */
  essential: true;
  /** Preferencias de búsqueda y UI */
  functional: boolean;
  /** Métricas anónimas de uso (futuro) */
  analytics: boolean;
}

export type CookieConsentInput = Pick<CookieConsent, "functional" | "analytics">;

export const DEFAULT_CONSENT: CookieConsent = {
  version: CONSENT_VERSION,
  updatedAt: new Date().toISOString(),
  essential: true,
  functional: false,
  analytics: false,
};

export const ACCEPT_ALL_CONSENT: CookieConsentInput = {
  functional: true,
  analytics: true,
};

export const ESSENTIAL_ONLY_CONSENT: CookieConsentInput = {
  functional: false,
  analytics: false,
};

export function buildConsent(input: CookieConsentInput): CookieConsent {
  return {
    version: CONSENT_VERSION,
    updatedAt: new Date().toISOString(),
    essential: true,
    functional: input.functional,
    analytics: input.analytics,
  };
}

export function loadConsent(): CookieConsent | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(CONSENT_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as CookieConsent;
    if (parsed.version !== CONSENT_VERSION) return null;
    return parsed;
  } catch {
    return null;
  }
}

export function saveConsent(consent: CookieConsent): void {
  localStorage.setItem(CONSENT_STORAGE_KEY, JSON.stringify(consent));
  window.dispatchEvent(new CustomEvent("findjob:cookie-consent", { detail: consent }));
}

export function hasConsentChoice(): boolean {
  return loadConsent() !== null;
}

export function withdrawOptionalConsent(): CookieConsent {
  const consent = buildConsent(ESSENTIAL_ONLY_CONSENT);
  saveConsent(consent);
  return consent;
}