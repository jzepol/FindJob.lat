import Link from "next/link";
import { Logo } from "./logo";

export function Footer() {
  return (
    <footer className="border-t border-border py-12">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-6 px-4 sm:flex-row sm:px-6 lg:px-8">
        <div className="text-center sm:text-left">
          <Logo size={28} />
          <p className="mt-2 text-sm text-muted">
            Agregador de empleos con IA para Latinoamérica
          </p>
        </div>
        <div className="flex gap-6 text-sm text-muted">
          <Link href="/jobs" className="hover:text-primary">
            Ofertas
          </Link>
          <Link href="/jobs/for-me" className="hover:text-primary">
            Para vos
          </Link>
          <Link href="/salarios" className="hover:text-primary">
            Salarios
          </Link>
          <Link href="/perfil" className="hover:text-primary">
            Perfil
          </Link>
        </div>
        <p className="text-xs text-muted">© {new Date().getFullYear()} Findjob.lat</p>
      </div>
    </footer>
  );
}