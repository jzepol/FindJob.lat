"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Briefcase,
  Check,
  FileText,
  Loader2,
  MapPin,
  Sparkles,
  User,
} from "lucide-react";
import { useAuth } from "@/components/auth-provider";
import { KarmaPanel } from "@/components/karma-panel";
import { ProfileAvatar } from "@/components/profile-avatar";
import { ProfileStepper } from "@/components/profile-stepper";
import { SUGGESTED_SKILLS } from "@/lib/constants";
import { CvUpload } from "@/components/cv-upload";
import { getKarma, getMatchStats, updateProfile, type KarmaInfo } from "@/lib/auth";
import type { MatchStats } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useToast } from "@/components/toast-provider";

const STEPS = [
  { id: 1, label: "Datos básicos", description: "Tu identidad", icon: User },
  { id: 2, label: "Subir CV", description: "Experiencia", icon: FileText },
  { id: 3, label: "Preferencias", description: "Matching IA", icon: MapPin },
];

function FieldLabel({
  children,
  hint,
  htmlFor,
}: {
  children: React.ReactNode;
  hint?: string;
  htmlFor?: string;
}) {
  return (
    <div className="mb-2">
      <label htmlFor={htmlFor} className="block text-sm font-medium text-foreground">
        {children}
      </label>
      {hint && <p className="mt-1 text-xs text-muted">{hint}</p>}
    </div>
  );
}

export default function PerfilPage() {
  const toast = useToast();
  const { user, loading, refresh } = useAuth();
  const [step, setStep] = useState(1);
  const [name, setName] = useState("");
  const [headline, setHeadline] = useState("");
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [cvText, setCvText] = useState("");
  const [skills, setSkills] = useState<string[]>([]);
  const [locations, setLocations] = useState<string[]>([]);
  const [karma, setKarma] = useState<KarmaInfo | null>(null);
  const [matchStats, setMatchStats] = useState<MatchStats | null>(null);
  const [saving, setSaving] = useState(false);

  const oauthAvatar = user?.oauth_accounts[0]?.avatar_url ?? null;

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
      getMatchStats().then(setMatchStats).catch(() => {});
    }
  }, [user]);

  const estimatedScore = Math.min(
    94,
    40 + skills.length * 4 + (cvText.length > 100 ? 25 : 0) + (headline ? 10 : 0),
  );
  const matchScore = matchStats?.embedding_ready
    ? (matchStats.match_score ?? estimatedScore)
    : estimatedScore;

  const completedSteps = [name.trim().length > 0, cvText.length > 50, skills.length > 0].filter(
    Boolean,
  ).length;

  if (!loading && !user) {
    return (
      <div className="flex min-h-[70vh] flex-col items-center justify-center px-4 text-center">
        <div className="card-premium max-w-md rounded-2xl p-10">
          <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 ring-1 ring-primary/20">
            <User className="h-7 w-7 text-primary" />
          </div>
          <h1 className="font-display text-2xl font-bold tracking-tight">
            Tu perfil te espera
          </h1>
          <p className="mt-3 text-sm leading-relaxed text-muted">
            Iniciá sesión para guardar tu CV, personalizar el matching con IA y sumar karma en la
            comunidad.
          </p>
          <Link href="/auth/login" className="btn-primary mt-8 inline-flex items-center gap-2">
            Ingresar
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    );
  }

  function toggleSkill(skill: string) {
    setSkills((s) =>
      s.includes(skill) ? s.filter((x) => x !== skill) : [...s, skill],
    );
  }

  function handleAvatarFile(file: File) {
    const reader = new FileReader();
    reader.onload = () => setAvatarPreview(String(reader.result));
    reader.readAsDataURL(file);
  }

  return (
    <div className="relative min-h-screen">
      <div className="hero-section pointer-events-none absolute inset-x-0 top-0 h-72 opacity-60" aria-hidden />
      <div className="hero-grid pointer-events-none absolute inset-x-0 top-0 h-72 opacity-40" aria-hidden />

      <div className="relative mx-auto max-w-5xl px-4 py-10 sm:px-6 sm:py-14 lg:px-8">
        {/* Header */}
        <div className="mb-8 flex flex-col gap-6 sm:mb-10 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-primary">
              Cuenta
            </p>
            <h1 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">
              Tu perfil
            </h1>
            <p className="mt-2 max-w-lg text-sm leading-relaxed text-foreground-secondary">
              Completá los pasos para activar el matching semántico con IA y desbloquear funciones
              de la comunidad.
            </p>
          </div>
          <div className="flex items-center gap-3 rounded-xl border border-border bg-surface/80 px-4 py-3 backdrop-blur-sm">
            <Briefcase className="h-4 w-4 text-primary" />
            <div className="text-sm">
              <span className="font-medium text-foreground">{completedSteps}/3</span>
              <span className="text-muted"> pasos completados</span>
            </div>
          </div>
        </div>

        <div className="grid gap-8 lg:grid-cols-[minmax(0,300px)_1fr] lg:gap-10">
          {/* Sidebar: Karma */}
          <aside className="space-y-6 lg:sticky lg:top-24 lg:self-start">
            {karma && <KarmaPanel karma={karma} />}
            <div className="hidden rounded-xl border border-border bg-surface-2/50 p-4 lg:block">
              <p className="text-xs leading-relaxed text-muted">
                <strong className="text-foreground-secondary">Tip:</strong> un perfil completo mejora
                la precisión del matching y te acerca más rápido a los 50 puntos de karma.
              </p>
            </div>
          </aside>

          {/* Main */}
          <div className="min-w-0 space-y-6">
            <div className="card-premium rounded-2xl p-4 sm:p-5">
              <ProfileStepper steps={STEPS} current={step} onStep={setStep} />
            </div>

            <div className="card-premium rounded-2xl p-6 sm:p-8">
              {step === 1 && (
                <div className="space-y-8">
                  <div>
                    <h2 className="font-display text-xl font-bold tracking-tight sm:text-2xl">
                      Datos básicos
                    </h2>
                    <p className="mt-1.5 text-sm text-muted">
                      Esta información aparece en tu perfil y mejora las recomendaciones de IA.
                    </p>
                  </div>

                  <div className="flex flex-col gap-8 sm:flex-row sm:items-start">
                    <ProfileAvatar
                      name={name || user?.email || "?"}
                      imageUrl={oauthAvatar}
                      preview={avatarPreview}
                      onFileSelect={handleAvatarFile}
                    />

                    <div className="min-w-0 flex-1 space-y-6">
                      <div>
                        <FieldLabel
                          htmlFor="full-name"
                          hint="Tu nombre como querés que lo vean las empresas."
                        >
                          Nombre completo
                        </FieldLabel>
                        <input
                          id="full-name"
                          value={name}
                          onChange={(e) => setName(e.target.value)}
                          className="input-field"
                          placeholder="Juan Pérez"
                        />
                      </div>
                      <div>
                        <FieldLabel
                          htmlFor="headline"
                          hint="Una línea que resuma tu rol y stack principal."
                        >
                          Headline profesional
                        </FieldLabel>
                        <input
                          id="headline"
                          value={headline}
                          onChange={(e) => setHeadline(e.target.value)}
                          className="input-field"
                          placeholder="Desarrollador Full Stack · Python & React"
                        />
                      </div>
                      {user?.email && (
                        <div>
                          <FieldLabel hint="Vinculado a tu cuenta. No editable por ahora.">
                            Email
                          </FieldLabel>
                          <div className="input-field cursor-default bg-surface-2/40 text-muted">
                            {user.email}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {step === 2 && (
                <div className="space-y-6">
                  <div>
                    <h2 className="font-display text-xl font-bold tracking-tight sm:text-2xl">
                      Subí tu CV
                    </h2>
                    <p className="mt-1.5 text-sm text-muted">
                      <strong className="text-primary">Gemini</strong> lee tu PDF/TXT, extrae skills y
                      genera el embedding para matching con ofertas. Primera carga:{" "}
                      <strong className="text-primary">+25 karma</strong>.
                    </p>
                  </div>

                  <CvUpload
                    cvText={cvText}
                    onCvChange={setCvText}
                    onUploaded={async ({
                      filename,
                      chars,
                      karmaGained,
                      parsedBy,
                      embeddingReady,
                      skills: extractedSkills,
                      headline: extractedHeadline,
                      fullName: extractedName,
                    }) => {
                      if (extractedName && !name.trim()) setName(extractedName);
                      if (extractedHeadline && !headline.trim()) setHeadline(extractedHeadline);
                      if (extractedSkills.length > 0) {
                        setSkills((prev) => {
                          const merged = [...prev];
                          for (const s of extractedSkills) {
                            if (!merged.some((x) => x.toLowerCase() === s.toLowerCase())) {
                              merged.push(s);
                            }
                          }
                          return merged;
                        });
                      }
                      await refresh();
                      const k = await getKarma();
                      setKarma(k);
                      const karmaNote =
                        karmaGained > 0 ? ` Sumaste ${karmaGained} puntos de karma.` : "";
                      toast(
                        `${parsedBy === "gemini" ? "Gemini" : "El sistema"} analizó tu CV (${chars.toLocaleString("es-AR")} caracteres).${
                          embeddingReady ? " Embedding listo para matching." : ""
                        }${karmaNote}`,
                        {
                          variant: "success",
                          title: embeddingReady ? "¡CV procesado!" : "¡CV cargado!",
                        },
                      );
                    }}
                    onError={(msg) =>
                      toast(msg, { variant: "error", title: "No pudimos leer el CV" })
                    }
                  />
                </div>
              )}

              {step === 3 && (
                <div className="space-y-8">
                  <div>
                    <h2 className="font-display text-xl font-bold tracking-tight sm:text-2xl">
                      Preferencias
                    </h2>
                    <p className="mt-1.5 text-sm text-muted">
                      Ajustá skills y ubicaciones para afinar las ofertas que te sugerimos.
                    </p>
                  </div>

                  <div>
                    <FieldLabel hint="Seleccioná las que mejor describan tu perfil.">
                      Skills principales
                    </FieldLabel>
                    <div className="flex flex-wrap gap-2">
                      {SUGGESTED_SKILLS.map((skill) => (
                        <button
                          key={skill}
                          type="button"
                          onClick={() => toggleSkill(skill)}
                          className={cn(
                            "rounded-lg border px-3.5 py-2 text-sm font-medium transition-all",
                            skills.includes(skill)
                              ? "border-secondary/40 bg-secondary/10 text-secondary shadow-sm"
                              : "border-border bg-surface-2/50 text-foreground-secondary hover:border-primary/30",
                          )}
                        >
                          {skills.includes(skill) && (
                            <Check className="mr-1.5 inline h-3.5 w-3.5" />
                          )}
                          {skill}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <FieldLabel hint="Presioná Enter para agregar cada ubicación.">
                      Ubicaciones preferidas
                    </FieldLabel>
                    <input
                      className="input-field"
                      placeholder="Buenos Aires, Remoto LATAM, Ciudad de México..."
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          const v = (e.target as HTMLInputElement).value.trim();
                          if (v && !locations.includes(v)) {
                            setLocations([...locations, v]);
                            (e.target as HTMLInputElement).value = "";
                          }
                        }
                      }}
                    />
                    {locations.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {locations.map((loc) => (
                          <button
                            key={loc}
                            type="button"
                            onClick={() => setLocations(locations.filter((l) => l !== loc))}
                            className="rounded-lg border border-primary/25 bg-primary/10 px-3 py-1.5 text-xs font-medium text-primary transition hover:bg-primary/15"
                          >
                            {loc} ×
                          </button>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="overflow-hidden rounded-2xl border border-primary/20 bg-gradient-to-br from-primary/10 via-surface to-secondary/10 p-6 text-center sm:p-8">
                    <Sparkles className="mx-auto mb-3 h-7 w-7 text-primary" />
                    <p className="text-sm font-medium text-foreground-secondary">
                      {matchStats?.embedding_ready
                        ? "Compatibilidad con ofertas"
                        : "Score de matching estimado"}
                    </p>
                    <p className="mt-1 font-mono text-5xl font-bold tracking-tight text-primary sm:text-6xl">
                      {matchScore}%
                    </p>
                    <p className="mx-auto mt-3 max-w-xs text-xs leading-relaxed text-muted">
                      {matchStats?.embedding_ready ? (
                        <>
                          Promedio de tus 5 mejores matches entre{" "}
                          {matchStats.offers_analyzed.toLocaleString("es-AR")} ofertas.
                          {matchStats.strong_matches > 0 && (
                            <> {matchStats.strong_matches} con ≥70% compatibilidad.</>
                          )}
                        </>
                      ) : (
                        "Subí tu CV para calcular compatibilidad real con IA."
                      )}
                    </p>
                  </div>
                </div>
              )}

              {/* Navigation */}
              <div className="mt-10 flex items-center justify-between gap-4 border-t border-border pt-8">
                <button
                  type="button"
                  disabled={step === 1}
                  onClick={() => setStep((s) => s - 1)}
                  className="btn-ghost inline-flex items-center gap-2 disabled:pointer-events-none disabled:opacity-30"
                >
                  <ArrowLeft className="h-4 w-4" />
                  Anterior
                </button>

                {step < 3 ? (
                  <button
                    type="button"
                    onClick={() => setStep((s) => s + 1)}
                    className="btn-primary inline-flex items-center gap-2"
                  >
                    Siguiente
                    <ArrowRight className="h-4 w-4" />
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
                        const [k, ms] = await Promise.all([getKarma(), getMatchStats()]);
                        setKarma(k);
                        setMatchStats(ms);
                        toast("Tu perfil quedó actualizado y listo para matching con IA.", {
                          variant: "success",
                          title: "¡Perfil guardado!",
                        });
                      } catch {
                        toast("No pudimos guardar los cambios. Intentá de nuevo.", {
                          variant: "error",
                          title: "Error al guardar",
                        });
                      } finally {
                        setSaving(false);
                      }
                    }}
                    className="btn-primary inline-flex min-w-[140px] items-center justify-center gap-2 disabled:opacity-60"
                  >
                    {saving ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Guardando...
                      </>
                    ) : (
                      <>
                        <Check className="h-4 w-4" />
                        Guardar perfil
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}