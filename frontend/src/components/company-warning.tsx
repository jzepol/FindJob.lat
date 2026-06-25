import { AlertTriangle } from "lucide-react";
import type { CompanyWarning } from "@/lib/auth";
import { cn } from "@/lib/utils";

const ISSUE_LABELS: Record<string, string> = {
  ghost_job: "Puesto fantasma",
  high_turnover: "Alta rotación",
  misleading_salary: "Salario engañoso",
  ats_black_hole: "Proceso opaco (ATS)",
  other: "Otros reportes",
};

export function CompanyWarningBanner({
  warning,
  className,
}: {
  warning: CompanyWarning;
  className?: string;
}) {
  const isHigh = warning.severity === "high";

  return (
    <div
      className={cn(
        "rounded-2xl border p-4",
        isHigh
          ? "border-danger/40 bg-danger/10"
          : "border-warning/40 bg-warning/10",
        className,
      )}
    >
      <div className="flex gap-3">
        <AlertTriangle
          className={cn("h-5 w-5 shrink-0", isHigh ? "text-danger" : "text-warning")}
        />
        <div>
          <p className="font-display text-sm font-bold">
            Advertencia de la comunidad — {warning.company}
          </p>
          <p className="mt-1 text-sm text-foreground/80">{warning.message}</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {Object.entries(warning.breakdown).map(([type, count]) => (
              <span
                key={type}
                className="rounded-full border border-border bg-surface-2 px-2 py-0.5 text-xs"
              >
                {ISSUE_LABELS[type] ?? type}: {count}
              </span>
            ))}
          </div>
          <p className="mt-2 text-xs text-muted">
            {warning.verified_reports} reportes verificados · Investigá antes de aplicar
          </p>
        </div>
      </div>
    </div>
  );
}