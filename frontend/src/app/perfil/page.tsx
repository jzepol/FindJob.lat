"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  Check,
  ChevronRight,
  FileText,
  MapPin,
  Sparkles,
  Upload,
  User,
} from "lucide-react";
import { useAuth } from "@/components/auth-provider";
import { SUGGESTED_SKILLS } from "@/lib/constants";
import { getKarma, updateProfile, type KarmaInfo } from "@/lib/auth";
import { cn } from "@/lib/utils";
import { useToast } from "@/components/toast-provider";

const STEPS = [
  { id: 1, label: "Datos básicos", icon: User },
  { id: 2, label: "Subir CV", icon: FileText },
  { id: 3, label: "Preferencias", icon: MapPin },
];

export default function PerfilPage() {
  const toast = useToast();
  const { user, loading, refresh } = useAuth();
  const [step, setStep] = useState(1);
  const [name, setName] = useState("");
  const [headline, setHeadline] = useState("");
  const [cvText, setCvText] = useState("");
  const [skills, setSkills] = useState<string[]>([]);
  const [locations, setLocations] = useState<string[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const [karma, setKarma] = useState<KarmaInfo | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (user?.profile) {
      setName(user.profile.full_name ?? "");
      setHeadline(user.profile.headline ?? "");
      setCvText(user.profile.cv_text ?? "");
      setSkills(user.profile.skills ?? []);
      setLocations(user.profile.preferred_locations ?? []);
    }
    if (user) {
      getKarma().then(setKarma).catch(() => {});
    }
  }, [user]);

  const matchScore = Math.min(
    94,
    40 + skills.length * 4 + (cvText.length > 100 ? 25 : 0) + (headline ? 10 : 0),
  );

  if (!loading && !user) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center px-4 text-center">
        <h1 className="font-display text-2xl font-bold">Iniciá sesión para tu perfil</h1>
        <p className="mt-2 text-muted">Necesitás una cuenta para guardar CV y ganar karma</p>
        <Link
          href="/auth/login"
          className="mt-6 rounded-xl bg-primary px-6 py-3 text-sm font-semibold text-white"
        >
          Ingresar con Google o email
        </Link>
      </div>
    );
  }

  function toggleSkill(skill: string) {
    setSkills((s) =>
      s.includes(skill) ? s.filter((x) => x !== skill) : [...s, skill],
    );
  }

  function handleFile(file: File) {
    const reader = new FileReader();
    reader.onload = () => {
      setCvText(String(reader.result).slice(0, 5000));
      toast("CV cargado correctamente");
    };
    reader.readAsText(file);
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
      <div className="mb-10 text-center">
        <h1 className="font-display text-3xl font-bold">Tu perfil</h1>
        <p className="mt-2 text-muted">
          Completá tu perfil para activar el matching con IA
        </p>
        {karma && (
          <div className="mx-auto mt-4 inline-flex items-center gap-3 rounded-full border border-primary/30 bg-primary/10 px-4 py-2 text-sm">
            <span className="font-mono font-bold text-primary">{karma.score} karma</span>
            {karma.can_report ? (
              <span className="text-primary">✓ Podés reportar empresas</span>
            ) : (
              <span className="text-muted">
                Faltan {karma.points_needed} para reportar
              </span>
            )}
          </div>
        )}
      </div>

      <div className="mb-10 flex items-center justify-center gap-2 sm:gap-4">
        {STEPS.map((s, i) => (
          <div key={s.id} className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setStep(s.id)}
              className={cn(
                "flex items-center gap-2 rounded-full border px-4 py-2 text-sm transition",
                step === s.id
                  ? "border-primary bg-primary/15 text-primary"
                  : step > s.id
                    ? "border-primary/30 text-primary/70"
                    : "border-border text-muted",
              )}
            >
              {step > s.id ? (
                <Check className="h-4 w-4" />
              ) : (
                <s.icon className="h-4 w-4" />
              )}
              <span className="hidden sm:inline">{s.label}</span>
              <span className="sm:hidden">{s.id}</span>
            </button>
            {i < STEPS.length - 1 && (
              <ChevronRight className="h-4 w-4 text-muted" />
            )}
          </div>
        ))}
      </div>

      <div className="glass rounded-2xl p-6 sm:p-8">
        {step === 1 && (
          <div className="space-y-5">
            <h2 className="font-display text-xl font-bold">Datos básicos</h2>
            <div>
              <label className="mb-1.5 block text-xs text-muted">Nombre completo</label>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full rounded-xl bg-surface-2 px-4 py-3 text-sm outline-none ring-primary/50 focus:ring-2"
                placeholder="Juan Pérez"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs text-muted">Headline profesional</label>
              <input
                value={headline}
                onChange={(e) => setHeadline(e.target.value)}
                className="w-full rounded-xl bg-surface-2 px-4 py-3 text-sm outline-none ring-primary/50 focus:ring-2"
                placeholder="Desarrollador Full Stack · Python & React"
              />
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-5">
            <h2 className="font-display text-xl font-bold">Subí tu CV</h2>
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragOver(false);
                const file = e.dataTransfer.files[0];
                if (file) handleFile(file);
              }}
              className={cn(
                "flex flex-col items-center justify-center rounded-2xl border-2 border-dashed py-16 transition",
                dragOver ? "border-primary bg-primary/5" : "border-border",
              )}
            >
              <Upload className="mb-4 h-10 w-10 text-primary" />
              <p className="font-medium">Arrastrá tu CV acá</p>
              <p className="mt-1 text-sm text-muted">PDF o TXT · máx. 5 MB</p>
              <label className="mt-4 cursor-pointer rounded-xl bg-primary px-5 py-2 text-sm font-medium text-white">
                Seleccionar archivo
                <input
                  type="file"
                  accept=".txt,.pdf"
                  className="hidden"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) handleFile(file);
                  }}
                />
              </label>
            </div>
            {cvText && (
              <textarea
                value={cvText}
                onChange={(e) => setCvText(e.target.value)}
                rows={6}
                className="w-full rounded-xl bg-surface-2 p-4 text-xs outline-none"
                placeholder="O pegá el texto de tu CV..."
              />
            )}
          </div>
        )}

        {step === 3 && (
          <div className="space-y-6">
            <h2 className="font-display text-xl font-bold">Preferencias</h2>
            <div>
              <label className="mb-2 block text-xs text-muted">Skills</label>
              <div className="flex flex-wrap gap-2">
                {SUGGESTED_SKILLS.map((skill) => (
                  <button
                    key={skill}
                    type="button"
                    onClick={() => toggleSkill(skill)}
                    className={cn(
                      "rounded-full border px-3 py-1.5 text-xs transition",
                      skills.includes(skill)
                        ? "border-secondary bg-secondary/15 text-secondary"
                        : "border-border text-muted hover:border-foreground-secondary/40",
                    )}
                  >
                    {skill}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="mb-1.5 block text-xs text-muted">Ubicaciones preferidas</label>
              <input
                className="w-full rounded-xl bg-surface-2 px-4 py-3 text-sm outline-none"
                placeholder="Buenos Aires, Remoto LATAM..."
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    const v = (e.target as HTMLInputElement).value.trim();
                    if (v && !locations.includes(v)) {
                      setLocations([...locations, v]);
                      (e.target as HTMLInputElement).value = "";
                    }
                  }
                }}
              />
              <div className="mt-2 flex flex-wrap gap-2">
                {locations.map((loc) => (
                  <span
                    key={loc}
                    className="rounded-full bg-primary/15 px-3 py-1 text-xs text-primary"
                  >
                    {loc}
                  </span>
                ))}
              </div>
            </div>

            <div
              className="rounded-2xl p-6 text-center"
              style={{
                background:
                  "linear-gradient(135deg, rgba(20,184,166,0.12), rgba(99,102,241,0.12))",
                border: "1px solid rgba(20,184,166,0.25)",
              }}
            >
              <Sparkles className="mx-auto mb-2 h-6 w-6 text-primary" />
              <p className="text-sm text-muted">Score de matching estimado</p>
              <p className="font-mono text-5xl font-bold text-primary">{matchScore}%</p>
              <p className="mt-2 text-xs text-muted">
                Basado en tu CV y preferencias · se activa con auth
              </p>
            </div>
          </div>
        )}

        <div className="mt-8 flex justify-between">
          <button
            type="button"
            disabled={step === 1}
            onClick={() => setStep((s) => s - 1)}
            className="rounded-xl border border-border px-5 py-2.5 text-sm disabled:opacity-30"
          >
            Anterior
          </button>
          {step < 3 ? (
            <button
              type="button"
              onClick={() => setStep((s) => s + 1)}
              className="rounded-xl bg-primary px-5 py-2.5 text-sm font-medium text-white"
            >
              Siguiente
            </button>
          ) : (
            <button
              type="button"
              disabled={saving}
              onClick={async () => {
                setSaving(true);
                try {
                  await updateProfile({
                    full_name: name,
                    headline,
                    cv_text: cvText,
                    skills,
                    preferred_locations: locations,
                  });
                  await refresh();
                  const k = await getKarma();
                  setKarma(k);
                  toast("Perfil guardado — karma actualizado");
                } catch {
                  toast("Error al guardar perfil");
                } finally {
                  setSaving(false);
                }
              }}
              className="rounded-xl bg-primary px-5 py-2.5 text-sm font-medium text-white disabled:opacity-50"
            >
              {saving ? "Guardando..." : "Guardar perfil"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}