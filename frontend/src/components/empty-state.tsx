import { Briefcase, Search } from "lucide-react";
import Link from "next/link";

export function EmptyState({
  title = "No encontramos ofertas",
  description = "Probá ajustar los filtros o ampliar la búsqueda.",
}: {
  title?: string;
  description?: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div
        className="mb-6 flex h-20 w-20 items-center justify-center rounded-3xl"
        style={{
          background: "linear-gradient(135deg, rgba(20,184,166,0.12), rgba(99,102,241,0.12))",
          border: "1px solid var(--border)",
        }}
      >
        <Briefcase className="h-9 w-9 text-primary" />
      </div>
      <h3 className="font-display text-xl font-bold">{title}</h3>
      <p className="mt-2 max-w-sm text-muted">{description}</p>
      <Link
        href="/jobs"
        className="mt-6 inline-flex items-center gap-2 rounded-full bg-primary px-5 py-2.5 text-sm font-medium text-white transition hover:bg-primary-hover"
      >
        <Search className="h-4 w-4" />
        Explorar todas las ofertas
      </Link>
    </div>
  );
}