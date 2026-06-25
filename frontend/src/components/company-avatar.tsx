import { cn } from "@/lib/utils";

export function CompanyAvatar({
  company,
  className,
  size = "md",
}: {
  company: string;
  className?: string;
  size?: "sm" | "md" | "lg";
}) {
  const initial = (company.replace(/^—$/, "?")[0] ?? "?").toUpperCase();
  const hash = company.split("").reduce((a, c) => a + c.charCodeAt(0), 0);

  const sizeClasses = {
    sm: "h-10 w-10 rounded-xl text-sm",
    md: "h-12 w-12 rounded-2xl text-base",
    lg: "h-14 w-14 rounded-2xl text-lg",
  };

  const gradients = [
    "from-primary/25 to-secondary/15",
    "from-secondary/25 to-primary/15",
    "from-primary/20 to-accent/10",
  ];
  const gradient = gradients[hash % gradients.length];

  return (
    <div
      className={cn(
        "relative flex shrink-0 items-center justify-center bg-gradient-to-br font-display font-bold text-foreground ring-1 ring-border",
        sizeClasses[size],
        gradient,
        className,
      )}
    >
      <span className="relative z-10">{initial}</span>
      <div className="absolute inset-0 rounded-[inherit] bg-surface/40" />
    </div>
  );
}