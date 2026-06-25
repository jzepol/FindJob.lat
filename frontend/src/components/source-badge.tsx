import { ExternalLink } from "lucide-react";
import type { Source } from "@/lib/types";

const SOURCE_COLORS: Record<string, string> = {
  computrabajo: "text-orange-400",
  bumeran: "text-blue-400",
  remoteok: "text-emerald-400",
};

export function SourceBadge({ source }: { source: Source }) {
  return (
    <span
      className={`inline-flex items-center gap-1 text-xs ${SOURCE_COLORS[source.slug] ?? "text-muted"}`}
    >
      <ExternalLink className="h-3 w-3" />
      {source.name}
    </span>
  );
}