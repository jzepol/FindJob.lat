"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { exchangeOAuthCode } from "@/lib/auth";
import { useAuth } from "@/components/auth-provider";

function CallbackHandler() {
  const router = useRouter();
  const params = useSearchParams();
  const { refresh } = useAuth();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const oauthError = params.get("error");
    if (oauthError) {
      router.replace(`/auth/login?error=${encodeURIComponent(oauthError)}`);
      return;
    }

    const code = params.get("code");
    if (!code) {
      router.replace("/auth/login");
      return;
    }

    exchangeOAuthCode(code)
      .then(() => refresh())
      .then(() => router.replace("/perfil"))
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Error al iniciar sesión");
      });
  }, [params, refresh, router]);

  if (error) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 px-4">
        <p className="text-danger">{error}</p>
        <button
          type="button"
          onClick={() => router.replace("/auth/login")}
          className="btn-primary"
        >
          Volver al login
        </button>
      </div>
    );
  }

  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <p className="text-muted">Completando inicio de sesión...</p>
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense>
      <CallbackHandler />
    </Suspense>
  );
}