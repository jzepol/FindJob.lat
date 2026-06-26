"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  ACCEPT_ALL_CONSENT,
  buildConsent,
  ESSENTIAL_ONLY_CONSENT,
  hasConsentChoice,
  loadConsent,
  saveConsent,
  withdrawOptionalConsent,
  type CookieConsent,
  type CookieConsentInput,
} from "@/lib/cookie-consent";
import { CookieBanner } from "./cookie-banner";

interface CookieContextValue {
  consent: CookieConsent | null;
  ready: boolean;
  acceptAll: () => void;
  acceptEssentialOnly: () => void;
  savePreferences: (input: CookieConsentInput) => void;
  withdrawConsent: () => void;
  openBanner: () => void;
  bannerOpen: boolean;
  closeBanner: () => void;
}

const CookieContext = createContext<CookieContextValue | null>(null);

export function CookieProvider({ children }: { children: ReactNode }) {
  const [consent, setConsent] = useState<CookieConsent | null>(null);
  const [ready, setReady] = useState(false);
  const [bannerOpen, setBannerOpen] = useState(false);

  useEffect(() => {
    const stored = loadConsent();
    setConsent(stored);
    setBannerOpen(!hasConsentChoice());
    setReady(true);

    const onUpdate = (e: Event) => {
      const detail = (e as CustomEvent<CookieConsent>).detail;
      setConsent(detail);
    };
    window.addEventListener("findjob:cookie-consent", onUpdate);
    return () => window.removeEventListener("findjob:cookie-consent", onUpdate);
  }, []);

  const persist = useCallback((input: CookieConsentInput) => {
    const next = buildConsent(input);
    saveConsent(next);
    setConsent(next);
    setBannerOpen(false);
  }, []);

  const value = useMemo<CookieContextValue>(
    () => ({
      consent,
      ready,
      acceptAll: () => persist(ACCEPT_ALL_CONSENT),
      acceptEssentialOnly: () => persist(ESSENTIAL_ONLY_CONSENT),
      savePreferences: persist,
      withdrawConsent: () => {
        const next = withdrawOptionalConsent();
        setConsent(next);
      },
      openBanner: () => setBannerOpen(true),
      bannerOpen,
      closeBanner: () => setBannerOpen(false),
    }),
    [consent, ready, persist, bannerOpen],
  );

  return (
    <CookieContext.Provider value={value}>
      {children}
      {ready && bannerOpen && <CookieBanner />}
    </CookieContext.Provider>
  );
}

export function useCookieConsent(): CookieContextValue {
  const ctx = useContext(CookieContext);
  if (!ctx) {
    throw new Error("useCookieConsent debe usarse dentro de CookieProvider");
  }
  return ctx;
}