"use client";

import Link from "next/link";
import { Cookie } from "lucide-react";
import { useState } from "react";
import { useCookieConsent } from "./cookie-provider";
import { CookiePreferencesPanel } from "./cookie-preferences-panel";

export function CookieBanner() {
  const { acceptAll, acceptEssentialOnly, closeBanner } = useCookieConsent();
  const [customize, setCustomize] = useState(false);

  if (customize) {
    return (
      <div className="fixed inset-x-0 bottom-0 z-[100] p-4 sm:p-6">
        <div className="mx-auto max-w-2xl rounded-2xl border border-border bg-surface/95 p-5 shadow-2xl backdrop-blur-xl sm:p-6">
          <CookiePreferencesPanel
            onSaved={closeBanner}
            onCancel={() => setCustomize(false)}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-x-0 bottom-0 z-[100] p-4 sm:p-6">
      <div className="mx-auto flex max-w-4xl flex-col gap-4 rounded-2xl border border-border bg-surface/95 p-5 shadow-2xl backdrop-blur-xl sm:flex-row sm:items-center sm:gap-6 sm:p-6">
        <div className="flex min-w-0 flex-1 gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/15 text-primary">
            <Cookie className="h-5 w-5" />
          </div>
          <div className="min-w-0 text-sm leading-relaxed text-foreground-secondary">
            <p className="font-medium text-foreground">Usamos cookies</p>
            <p className="mt-1 text-muted">
              Las necesarias mantienen tu sesión y preferencias. Las opcionales mejoran la
              experiencia y nos ayudan a entender el uso del sitio.{" "}
              <Link href="/legal/cookies" className="text-primary hover:underline">
                Política de cookies
              </Link>
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2 sm:shrink-0">
          <button
            type="button"
            onClick={() => setCustomize(true)}
            className="rounded-xl border border-border px-4 py-2.5 text-sm font-medium transition hover:border-primary/40"
          >
            Personalizar
          </button>
          <button
            type="button"
            onClick={acceptEssentialOnly}
            className="rounded-xl border border-border px-4 py-2.5 text-sm font-medium transition hover:border-primary/40"
          >
            Solo necesarias
          </button>
          <button
            type="button"
            onClick={acceptAll}
            className="rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-primary-hover"
          >
            Aceptar todas
          </button>
        </div>
      </div>
    </div>
  );
}