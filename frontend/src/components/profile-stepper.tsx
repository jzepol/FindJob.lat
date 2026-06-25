"use client";

import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

export type ProfileStep = {
  id: number;
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
};

export function ProfileStepper({
  steps,
  current,
  onStep,
}: {
  steps: ProfileStep[];
  current: number;
  onStep: (id: number) => void;
}) {
  return (
    <nav aria-label="Progreso del perfil" className="w-full">
      <ol className="flex items-stretch gap-0">
        {steps.map((step, index) => {
          const isActive = current === step.id;
          const isComplete = current > step.id;
          const isLast = index === steps.length - 1;

          return (
            <li key={step.id} className={cn("flex flex-1 items-center", !isLast && "min-w-0")}>
              <button
                type="button"
                onClick={() => onStep(step.id)}
                className={cn(
                  "group flex w-full flex-col items-center gap-2 rounded-xl px-2 py-3 transition sm:px-4",
                  isActive && "bg-primary/10",
                )}
              >
                <span
                  className={cn(
                    "flex h-10 w-10 items-center justify-center rounded-xl border-2 text-sm font-semibold transition-all",
                    isActive &&
                      "border-primary bg-primary text-white shadow-glow scale-105",
                    isComplete &&
                      !isActive &&
                      "border-primary/40 bg-primary/10 text-primary",
                    !isActive &&
                      !isComplete &&
                      "border-border bg-surface text-muted group-hover:border-primary/30",
                  )}
                >
                  {isComplete && !isActive ? (
                    <Check className="h-4 w-4" strokeWidth={3} />
                  ) : (
                    <step.icon className="h-4 w-4" />
                  )}
                </span>
                <span className="hidden text-center sm:block">
                  <span
                    className={cn(
                      "block text-xs font-semibold",
                      isActive ? "text-primary" : isComplete ? "text-foreground" : "text-muted",
                    )}
                  >
                    {step.label}
                  </span>
                  <span className="mt-0.5 block text-[10px] text-muted">{step.description}</span>
                </span>
                <span
                  className={cn(
                    "text-[10px] font-semibold sm:hidden",
                    isActive ? "text-primary" : "text-muted",
                  )}
                >
                  {step.id}/{steps.length}
                </span>
              </button>

              {!isLast && (
                <div
                  className={cn(
                    "mx-1 hidden h-0.5 w-full max-w-[48px] shrink rounded-full sm:block",
                    isComplete ? "bg-primary/50" : "bg-border",
                  )}
                  aria-hidden
                />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}