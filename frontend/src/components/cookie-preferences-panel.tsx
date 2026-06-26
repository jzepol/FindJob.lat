"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useCookieConsent } from "./cookie-provider";
import type { CookieConsentInput } from "@/lib/cookie-consent";

function Toggle({
  checked,
  disabled,
  onChange,
  label,
  description,
}: {
  checked: boolean;
  disabled?: boolean;
  onChange: (v: boolean) => void;
  label: string;
  description: string;
}) {
  return (
    <label
      className={`flex items-start justify-between gap-4 rounded-xl border border-border p-4 ${
        disabled ? "opacity-70" : "cursor-pointer hover:border-primary/25"
      }`}
    >
      <div>
        <p className="text-sm font-medium text-foreground">{label}</p>
        <p className="mt-1 text-xs leading-relaxed text-muted">{description}</p>
      </div>
      <input
        type="checkbox"
        checked={checked}
        disabled={disabled}
        onChange={(e) => onChange(e.target.checked)}
        className="mt-1 h-4 w-4 shrink-0 accent-primary"
      />
    </label>
  );
}

export function CookiePreferencesPanel({
  onSaved,
  onCancel,
  showWithdraw = true,
}: {
  onSaved?: () => void;
  onCancel?: () => void;
  showWithdraw?: boolean;
}) {
  const { consent, savePreferences, withdrawConsent } = useCookieConsent();
  const [functional, setFunctional] = useState(consent?.functional ?? false);
  const [analytics, setAnalytics] = useState(consent?.analytics ?? false);

  useEffect(() => {
    setFunctional(consent?.functional ?? false);
    setAnalytics(consent?.analytics ?? false);
  }, [consent]);

  function handleSave() {
    const input: CookieConsentInput = { functional, analytics };
    savePreferences(input);
    onSaved?.();
  }

  function handleWithdraw() {
    withdrawConsent();
    setFunctional(false);
    setAnalytics(false);
    onSaved?.();
  }

  return (
    <div className="space-y-4">
      <div>
        <h3 className="font-display text-lg font-bold">Preferencias de cookies</h3>
        <p className="mt-1 text-sm text-muted">
          Podés cambiar tu decisión en cualquier momento desde tu perfil.{" "}
          <Link href="/legal/cookies" className="text-primary hover:underline">
            Ver política completa
          </Link>
        </p>
      </div>

      <div className="space-y-3">
        <Toggle
          checked
          disabled
          onChange={() => {}}
          label="Necesarias"
          description="Sesión de usuario, seguridad y tema visual. No se pueden desactivar."
        />
        <Toggle
          checked={functional}
          onChange={setFunctional}
          label="Funcionales"
          description="Recordar filtros de búsqueda y preferencias de la interfaz."
        />
        <Toggle
          checked={analytics}
          onChange={setAnalytics}
          label="Analíticas"
          description="Estadísticas anónimas de uso para mejorar Findjob.lat."
        />
      </div>

      <div className="flex flex-wrap gap-2 pt-2">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="rounded-xl border border-border px-4 py-2.5 text-sm font-medium transition hover:border-primary/40"
          >
            Cancelar
          </button>
        )}
        <button
          type="button"
          onClick={handleSave}
          className="rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-primary-hover"
        >
          Guardar preferencias
        </button>
        {showWithdraw && consent && (consent.functional || consent.analytics) && (
          <button
            type="button"
            onClick={handleWithdraw}
            className="rounded-xl border border-danger/30 px-4 py-2.5 text-sm font-medium text-danger transition hover:bg-danger/10"
          >
            Retirar consentimiento opcional
          </button>
        )}
      </div>

      {consent?.updatedAt && (
        <p className="text-xs text-muted">
          Última actualización:{" "}
          {new Date(consent.updatedAt).toLocaleString("es-AR", {
            dateStyle: "medium",
            timeStyle: "short",
          })}
        </p>
      )}
    </div>
  );
}