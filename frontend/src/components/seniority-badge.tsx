import { cn, seniorityLabel } from "@/lib/utils";
import type { Seniority } from "@/lib/types";

export function SeniorityBadge({ seniority }: { seniority: Seniority }) {
  if (seniority === "unknown") return null;
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-lg border border-border bg-surface-2/80 px-2.5 py-1",
        "text-xs font-medium text-foreground-secondary",
      )}
    >
      {seniorityLabel(seniority)}
    </span>
  );
}