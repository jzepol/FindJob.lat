import { Briefcase, Building2, Globe2, Sparkles } from "lucide-react";
import { HeroSearch } from "./hero-search";
import type { Stats } from "@/lib/types";

export function HeroSection({ stats }: { stats: Stats }) {
  const trustItems = [
    {
      icon: Briefcase,
      value: stats.active_offers > 0 ? `${stats.active_offers.toLocaleString("es-AR")}+` : "1.000+",
      label: "ofertas activas",
    },
    {
      icon: Building2,
      value: stats.companies > 0 ? `${stats.companies.toLocaleString("es-AR")}+` : "500+",
      label: "empresas",
    },
    {
      icon: Globe2,
      value: "12",
      label: "países LATAM",
    },
  ];

  return (
    <section className="hero-section relative">
      <div className="hero-grid pointer-events-none absolute inset-0" aria-hidden />

      <div className="relative mx-auto max-w-5xl px-4 pb-20 pt-24 text-center sm:px-6 sm:pb-28 sm:pt-28 lg:px-8">
        <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-4 py-1.5 text-xs font-medium text-primary backdrop-blur-sm">
          <Sparkles className="h-3.5 w-3.5" />
          Matching semántico con IA · Actualizado en tiempo real
        </div>

        <h1 className="font-display text-[2.5rem] font-bold leading-[1.08] tracking-tight sm:text-5xl lg:text-[3.5rem]">
          <span className="block text-foreground">Tu próximo trabajo</span>
          <span className="gradient-text mt-1 block">en toda Latinoamérica</span>
        </h1>

        <p className="mx-auto mt-6 max-w-2xl text-base leading-relaxed text-foreground-secondary sm:text-lg">
          Un solo lugar para explorar ofertas de Computrabajo, Bumeran, Remote OK y más.
          Encontrá la oportunidad ideal con búsqueda inteligente.
        </p>

        <div className="mt-10 sm:mt-12">
          <HeroSearch />
        </div>

        <div className="mt-10 flex flex-wrap items-center justify-center gap-3 sm:gap-4">
          {trustItems.map((item) => (
            <div key={item.label} className="trust-pill">
              <item.icon className="h-4 w-4 text-primary" />
              <span className="font-display font-semibold text-foreground">{item.value}</span>
              <span className="text-muted">{item.label}</span>
            </div>
          ))}
        </div>
      </div>

      <div
        className="pointer-events-none absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-background to-transparent"
        aria-hidden
      />
    </section>
  );
}