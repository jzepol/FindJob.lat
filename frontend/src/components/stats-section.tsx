"use client";

import { useEffect, useState } from "react";
import type { Stats } from "@/lib/types";

function AnimatedNumber({ value }: { value: number }) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    const duration = 1200;
    const start = performance.now();
    const tick = (now: number) => {
      const progress = Math.min((now - start) / duration, 1);
      setDisplay(Math.floor(progress * value));
      if (progress < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }, [value]);

  return <span className="font-mono">{display.toLocaleString("es-AR")}</span>;
}

export function StatsSection({ stats }: { stats: Stats }) {
  const items = [
    { label: "ofertas activas", value: stats.active_offers },
    { label: "empresas", value: stats.companies },
    { label: "portales", value: stats.sources },
  ];

  return (
    <section className="py-16">
      <div className="mx-auto grid max-w-4xl grid-cols-1 gap-8 px-4 sm:grid-cols-3 sm:px-6">
        {items.map((item) => (
          <div key={item.label} className="text-center">
            <p className="font-display text-4xl font-bold text-primary sm:text-5xl">
              <AnimatedNumber value={item.value} />
            </p>
            <p className="mt-2 text-sm text-muted">{item.label}</p>
          </div>
        ))}
      </div>
    </section>
  );
}