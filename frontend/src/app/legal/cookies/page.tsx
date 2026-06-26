import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export const metadata = {
  title: "Política de cookies | Findjob.lat",
  description: "Información sobre el uso de cookies en Findjob.lat",
};

export default function CookiesPolicyPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6 lg:px-8">
      <Link
        href="/"
        className="mb-8 inline-flex items-center gap-1 text-sm text-muted hover:text-primary"
      >
        <ArrowLeft className="h-4 w-4" /> Inicio
      </Link>

      <h1 className="font-display text-3xl font-bold">Política de cookies</h1>
      <p className="mt-2 text-sm text-muted">Última actualización: junio 2026</p>

      <div className="prose prose-invert mt-10 max-w-none space-y-6 text-sm leading-relaxed text-foreground-secondary">
        <section>
          <h2 className="font-display text-xl font-semibold text-foreground">¿Qué son las cookies?</h2>
          <p>
            Las cookies son pequeños archivos que el sitio guarda en tu navegador para recordar
            información sobre tu visita: sesión, preferencias o estadísticas de uso.
          </p>
        </section>

        <section>
          <h2 className="font-display text-xl font-semibold text-foreground">Cookies que usamos</h2>
          <ul className="list-disc space-y-2 pl-5">
            <li>
              <strong className="text-foreground">Necesarias:</strong> cookie de sesión{" "}
              <code className="rounded bg-surface-2 px-1.5 py-0.5 text-xs">findjob_session</code>{" "}
              (httpOnly, para mantener tu login), y preferencia de tema en localStorage.
            </li>
            <li>
              <strong className="text-foreground">Funcionales:</strong> filtros de búsqueda y
              preferencias de interfaz guardadas localmente, solo si aceptás esta categoría.
            </li>
            <li>
              <strong className="text-foreground">Analíticas:</strong> métricas anónimas de uso
              (cuando estén activas), solo con tu consentimiento.
            </li>
          </ul>
        </section>

        <section>
          <h2 className="font-display text-xl font-semibold text-foreground">Tu control</h2>
          <p>
            Al entrar por primera vez verás un banner para aceptar, rechazar o personalizar cookies
            opcionales. Podés cambiar tu decisión en cualquier momento desde{" "}
            <Link href="/perfil" className="text-primary hover:underline">
              tu perfil
            </Link>{" "}
            → sección Privacidad y cookies, o retirar el consentimiento opcional.
          </p>
          <p>
            Las cookies necesarias para el login no pueden desactivarse mientras uses una cuenta
            autenticada; al cerrar sesión dejan de usarse para identificarte en nuevas visitas.
          </p>
        </section>

        <section>
          <h2 className="font-display text-xl font-semibold text-foreground">Conservación</h2>
          <p>
            La preferencia de consentimiento se guarda en tu navegador hasta que la modifiques o
            borres los datos del sitio. La sesión expira según la configuración del servidor (7
            días por defecto).
          </p>
        </section>

        <section>
          <h2 className="font-display text-xl font-semibold text-foreground">Más información</h2>
          <p>
            Consultá también nuestra{" "}
            <Link href="/legal/privacidad" className="text-primary hover:underline">
              política de privacidad
            </Link>
            . Para consultas: contacto vía los canales publicados en el sitio.
          </p>
        </section>
      </div>
    </div>
  );
}