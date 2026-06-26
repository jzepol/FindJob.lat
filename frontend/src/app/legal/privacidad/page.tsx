import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export const metadata = {
  title: "Política de privacidad | Findjob.lat",
  description: "Cómo tratamos tus datos personales en Findjob.lat",
};

export default function PrivacyPolicyPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6 lg:px-8">
      <Link
        href="/"
        className="mb-8 inline-flex items-center gap-1 text-sm text-muted hover:text-primary"
      >
        <ArrowLeft className="h-4 w-4" /> Inicio
      </Link>

      <h1 className="font-display text-3xl font-bold">Política de privacidad</h1>
      <p className="mt-2 text-sm text-muted">Última actualización: junio 2026</p>

      <div className="prose prose-invert mt-10 max-w-none space-y-6 text-sm leading-relaxed text-foreground-secondary">
        <section>
          <h2 className="font-display text-xl font-semibold text-foreground">Responsable</h2>
          <p>
            Findjob.lat es un agregador de ofertas laborales. Los datos que nos proporcionás se
            usan para ofrecerte búsqueda, matching con IA y funciones de cuenta.
          </p>
        </section>

        <section>
          <h2 className="font-display text-xl font-semibold text-foreground">Datos que recopilamos</h2>
          <ul className="list-disc space-y-2 pl-5">
            <li>Email y nombre al registrarte o vía Google OAuth.</li>
            <li>CV y perfil profesional (skills, preferencias) si los subís voluntariamente.</li>
            <li>Actividad de búsqueda y karma para funciones comunitarias.</li>
            <li>Reportes de empresas que envíes con tu cuenta.</li>
          </ul>
        </section>

        <section>
          <h2 className="font-display text-xl font-semibold text-foreground">Finalidad</h2>
          <p>
            Personalizar recomendaciones de empleo, mantener tu sesión, mejorar el servicio y
            moderar reportes comunitarios. El CV se procesa con IA (Google Gemini) para extraer
            datos y generar embeddings de matching semántico.
          </p>
        </section>

        <section>
          <h2 className="font-display text-xl font-semibold text-foreground">Tus derechos</h2>
          <p>
            Podés actualizar o eliminar información de tu perfil, retirar consentimiento de cookies
            opcionales y solicitar información sobre el tratamiento de tus datos. La gestión de
            cookies está en{" "}
            <Link href="/perfil" className="text-primary hover:underline">
              tu perfil
            </Link>
            .
          </p>
        </section>

        <section>
          <h2 className="font-display text-xl font-semibold text-foreground">Cookies</h2>
          <p>
            Detalle completo en la{" "}
            <Link href="/legal/cookies" className="text-primary hover:underline">
              política de cookies
            </Link>
            .
          </p>
        </section>
      </div>
    </div>
  );
}