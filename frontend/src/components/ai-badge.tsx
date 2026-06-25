import { Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

export function AiBadge({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium",
        "bg-primary/15 text-primary border border-primary/25",
        className,
      )}
    >
      <Sparkles className="h-3 w-3" />
      Powered by IA
    </span>
  );
}