import { PORTALS } from "@/lib/constants";
import { cn } from "@/lib/utils";

export function PortalsSection() {
  return (
    <section className="py-12">
      <p className="mb-6 text-center text-sm font-medium text-muted">
        Portales que agregamos
      </p>
      <div className="mx-auto flex max-w-3xl flex-wrap items-center justify-center gap-3 px-4">
        {PORTALS.map((portal) => (
          <span
            key={portal.slug}
            className={cn(
              "rounded-full border px-4 py-2 text-sm font-medium transition",
              portal.active
                ? "border-primary/30 bg-primary/10 text-primary"
                : "border-border bg-surface-2 text-muted",
            )}
          >
            {portal.name}
            {!portal.active && (
              <span className="ml-1.5 text-xs opacity-60">pronto</span>
            )}
          </span>
        ))}
      </div>
    </section>
  );
}