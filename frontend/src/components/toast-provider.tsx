"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { AlertCircle, Check, X } from "lucide-react";
import { cn } from "@/lib/utils";

export type ToastVariant = "success" | "error" | "info";

export interface ToastOptions {
  variant?: ToastVariant;
  title?: string;
  duration?: number;
}

interface Toast {
  id: number;
  message: string;
  title?: string;
  variant: ToastVariant;
  duration: number;
}

type ToastFn = (message: string, options?: ToastOptions) => void;

const ToastContext = createContext<ToastFn>(() => {});

function CelebrationToast({
  toast,
  onDismiss,
}: {
  toast: Toast;
  onDismiss: () => void;
}) {
  const [visible, setVisible] = useState(false);
  const isSuccess = toast.variant === "success";

  useEffect(() => {
    const enter = requestAnimationFrame(() => setVisible(true));
    const timer = setTimeout(() => {
      setVisible(false);
      setTimeout(onDismiss, 280);
    }, toast.duration);

    return () => {
      cancelAnimationFrame(enter);
      clearTimeout(timer);
    };
  }, [toast.duration, onDismiss]);

  return (
    <div
      className={cn(
        "fixed inset-0 z-[200] flex items-center justify-center p-6 transition-all duration-300",
        visible ? "bg-overlay/80 backdrop-blur-sm" : "bg-transparent pointer-events-none",
      )}
      onClick={() => {
        setVisible(false);
        setTimeout(onDismiss, 280);
      }}
      role="alertdialog"
      aria-live="assertive"
    >
      <div
        className={cn(
          "pointer-events-auto w-full max-w-sm rounded-3xl border bg-surface p-8 text-center shadow-card-hover transition-all duration-300",
          visible ? "celebration-enter scale-100 opacity-100" : "scale-90 opacity-0",
          isSuccess ? "border-primary/25" : "border-danger/25",
        )}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="relative mx-auto mb-6 flex h-24 w-24 items-center justify-center">
          <span
            className={cn(
              "celebration-ring absolute inset-0 rounded-full",
              isSuccess ? "bg-primary/15" : "bg-danger/15",
            )}
          />
          <span
            className={cn(
              "celebration-pop relative flex h-20 w-20 items-center justify-center rounded-full",
              isSuccess
                ? "bg-primary text-white shadow-glow"
                : "bg-danger text-white",
            )}
          >
            {isSuccess ? (
              <Check className="celebration-check h-10 w-10" strokeWidth={3} />
            ) : (
              <AlertCircle className="h-10 w-10" strokeWidth={2.5} />
            )}
          </span>
        </div>

        <h2 className="font-display text-xl font-bold tracking-tight text-foreground">
          {toast.title ?? (isSuccess ? "¡Listo!" : "Ups, algo falló")}
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-foreground-secondary">
          {toast.message}
        </p>

        <button
          type="button"
          onClick={() => {
            setVisible(false);
            setTimeout(onDismiss, 280);
          }}
          className={cn(
            "mt-6 w-full rounded-xl py-3 text-sm font-semibold text-white transition active:scale-[0.98]",
            isSuccess ? "bg-primary hover:bg-primary-hover" : "bg-danger",
          )}
        >
          Continuar
        </button>
      </div>
    </div>
  );
}

function InfoToast({
  toast,
  onDismiss,
}: {
  toast: Toast;
  onDismiss: () => void;
}) {
  return (
    <div
      className="info-toast-enter flex items-center gap-3 rounded-2xl border border-border-strong bg-surface px-4 py-3 text-sm shadow-card"
      role="status"
    >
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/15">
        <Check className="h-4 w-4 text-primary" />
      </span>
      <span className="text-foreground">{toast.message}</span>
      <button
        type="button"
        onClick={onDismiss}
        className="ml-1 text-muted transition hover:text-foreground"
        aria-label="Cerrar"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const dismiss = useCallback((id: number) => {
    setToasts((t) => t.filter((x) => x.id !== id));
  }, []);

  const toast = useCallback((message: string, options?: ToastOptions) => {
    const id = Date.now() + Math.random();
    const variant = options?.variant ?? "info";
    const duration =
      options?.duration ?? (variant === "info" ? 3200 : variant === "success" ? 2800 : 3400);

    setToasts((t) => [...t, { id, message, title: options?.title, variant, duration }]);

    if (variant === "info") {
      setTimeout(() => dismiss(id), duration);
    }
  }, [dismiss]);

  const celebration = toasts.find((t) => t.variant === "success" || t.variant === "error");
  const infoToasts = toasts.filter((t) => t.variant === "info");

  return (
    <ToastContext.Provider value={toast}>
      {children}

      {celebration && (
        <CelebrationToast
          key={celebration.id}
          toast={celebration}
          onDismiss={() => dismiss(celebration.id)}
        />
      )}

      {infoToasts.length > 0 && (
        <div className="fixed left-1/2 top-6 z-[150] flex w-full max-w-md -translate-x-1/2 flex-col gap-2 px-4">
          {infoToasts.map((t) => (
            <InfoToast key={t.id} toast={t} onDismiss={() => dismiss(t.id)} />
          ))}
        </div>
      )}
    </ToastContext.Provider>
  );
}

export function useToast() {
  return useContext(ToastContext);
}