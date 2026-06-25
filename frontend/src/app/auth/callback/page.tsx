"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";
import { setToken } from "@/lib/auth";
import { useAuth } from "@/components/auth-provider";

function CallbackHandler() {
  const router = useRouter();
  const params = useSearchParams();
  const { refresh } = useAuth();

  useEffect(() => {
    const error = params.get("error");
    if (error) {
      router.replace(`/auth/login?error=${encodeURIComponent(error)}`);
      return;
    }
    const token = params.get("token");
    if (token) {
      setToken(token);
      refresh().then(() => router.replace("/perfil"));
    } else {
      router.replace("/auth/login");
    }
  }, [params, refresh, router]);

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