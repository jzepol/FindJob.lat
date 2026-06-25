import { Building2, Globe, Shuffle } from "lucide-react";
import { cn, modalityLabel } from "@/lib/utils";
import type { Modality } from "@/lib/types";

const CONFIG: Record<
  Modality,
  { icon: typeof Globe; style: string }
> = {
  remote: {
    icon: Globe,
    style: "bg-primary/10 text-primary border-primary/25",
  },
  hybrid: {
    icon: Shuffle,
    style: "bg-secondary/10 text-secondary border-secondary/25",
  },
  on_site: {
    icon: Building2,
    style: "bg-surface-2 text-foreground-secondary border-border",
  },
  unknown: {
    icon: Building2,
    style: "bg-surface-2 text-muted border-border",
  },
};

export function ModalityBadge({ modality }: { modality: Modality }) {
  const { icon: Icon, style } = CONFIG[modality];

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-xs font-medium",
        style,
      )}
    >
      <Icon className="h-3 w-3" />
      {modalityLabel(modality)}
    </span>
  );
}