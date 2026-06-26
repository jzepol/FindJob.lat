"use client";

import { useCookieConsent } from "./cookie-provider";

export function CookieManageLink({ className }: { className?: string }) {
  const { openBanner } = useCookieConsent();

  return (
    <button
      type="button"
      onClick={openBanner}
      className={className ?? "hover:text-primary"}
    >
      Gestionar cookies
    </button>
  );
}