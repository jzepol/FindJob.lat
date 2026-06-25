"use client";

import { useState } from "react";
import { Flag, X } from "lucide-react";
import { getKarma, submitCompanyReport } from "@/lib/auth";
import { useAuth } from "./auth-provider";
import { useToast } from "./toast-provider";
import { cn } from "@/lib/utils";

const REPORT_TYPES = [
  { value: "ghost_job", label: "Puesto fantasma", desc: "La vacante no existe o solo captura CVs" },
  { value: "ats_black_hole", label: "Agujero negro ATS", desc: "Muchos postulantes, cero respuestas" },
  { value: "high_turnover", label: "Alta rotación", desc: "Renuncias frecuentes, mal clima" },
  { value: "misleading_salary", label: "Salario engañoso", desc: "Rango publicado no coincide" },
  { value: "other", label: "Otro", desc: "Otro problema con el proceso" },
];

export function ReportCompanyButton({
  offerId,
  companyName,
}: {
  offerId: string;
  companyName: string;
}) {
  const { user, refresh } = useAuth();
  const toast = useToast();
  const [open, setOpen] = useState(false);
  const [type, setType] = useState("ats_black_hole");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleOpen() {
    if (!user) {
      toast("Iniciá sesión para reportar");
      window.location.href = "/auth/login";
      return;
    }
    try {
      const karma = await getKarma();
      if (!karma.can_report) {
        toast(`Necesitás ${karma.points_needed} karma más para reportar`);
        return;
      }
    } catch {
      toast("Error al verificar karma");
      return;
    }
    setOpen(true);
  }

  async function handleSubmit() {
    setSubmitting(true);
    try {
      await submitCompanyReport({
        offer_id: offerId,
        company_name: companyName,
        report_type: type,
        description: description || undefined,
      });
      toast("Tu reporte fue registrado. Gracias por ayudar a la comunidad.", {
        variant: "success",
        title: "¡Reporte enviado!",
      });
      setOpen(false);
      await refresh();
    } catch (e) {
      toast(e instanceof Error ? e.message : "Error al reportar");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={handleOpen}
        className="flex w-full items-center justify-center gap-2 rounded-xl border border-accent/30 bg-accent/10 py-2.5 text-sm text-accent transition hover:bg-accent/20"
      >
        <Flag className="h-4 w-4" />
        Reportar empresa
      </button>

      {open && (
        <div className="overlay fixed inset-0 z-[200] flex items-center justify-center p-4">
          <div className="glass max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl p-6">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="font-display text-lg font-bold">Reportar {companyName}</h3>
              <button type="button" onClick={() => setOpen(false)}>
                <X className="h-5 w-5 text-muted" />
              </button>
            </div>

            <p className="mb-4 text-sm text-muted">
              Tu reporte ayuda a otros postulantes. Se verifica cuando varios usuarios
              independientes reportan lo mismo.
            </p>

            <div className="space-y-2">
              {REPORT_TYPES.map((rt) => (
                <button
                  key={rt.value}
                  type="button"
                  onClick={() => setType(rt.value)}
                  className={cn(
                    "w-full rounded-xl border p-3 text-left transition",
                    type === rt.value
                      ? "border-primary bg-primary/10"
                      : "border-border hover:border-foreground-secondary/40",
                  )}
                >
                  <p className="text-sm font-medium">{rt.label}</p>
                  <p className="text-xs text-muted">{rt.desc}</p>
                </button>
              ))}
            </div>

            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Detalle opcional (máx. 2000 chars)..."
              rows={3}
              className="mt-4 w-full rounded-xl bg-surface-2 p-3 text-sm outline-none"
            />

            <button
              type="button"
              disabled={submitting}
              onClick={handleSubmit}
              className="mt-4 w-full rounded-xl bg-accent py-3 text-sm font-semibold text-white disabled:opacity-50"
            >
              {submitting ? "Enviando..." : "Enviar reporte"}
            </button>
          </div>
        </div>
      )}
    </>
  );
}