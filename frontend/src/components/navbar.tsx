"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { LogOut, Menu, User, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { AiBadge } from "./ai-badge";
import { useAuth } from "./auth-provider";
import { Logo } from "./logo";
import { ThemeToggle } from "./theme-toggle";

const LINKS = [
  { href: "/jobs", label: "Ofertas" },
  { href: "/salarios", label: "Salarios" },
  { href: "/perfil", label: "Mi perfil" },
];

export function Navbar() {
  const pathname = usePathname();
  const { user, logout, loading } = useAuth();
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const displayName =
    user?.profile?.full_name ||
    user?.oauth_accounts[0]?.display_name ||
    user?.email?.split("@")[0];

  return (
    <header
      className={cn(
        "fixed inset-x-0 top-0 z-50 transition-all duration-300",
        scrolled ? "glass shadow-lg" : "bg-transparent",
      )}
      style={scrolled ? { boxShadow: "0 4px 24px -4px rgba(20, 184, 166, 0.15)" } : undefined}
    >
      <nav className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Logo size={32} />

        <div className="hidden items-center gap-8 md:flex">
          {LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "text-sm font-medium transition hover:text-primary",
                pathname === link.href ? "text-primary" : "text-muted",
              )}
            >
              {link.label}
            </Link>
          ))}
        </div>

        <div className="hidden items-center gap-3 md:flex">
          <AiBadge />
          <ThemeToggle />

          {!loading && user ? (
            <div className="flex items-center gap-2">
              <Link
                href="/perfil"
                className="flex items-center gap-2 rounded-xl border border-primary/30 bg-primary/10 px-3 py-2 text-sm"
              >
                <User className="h-4 w-4" />
                <span className="max-w-[100px] truncate">{displayName}</span>
                <span className="font-mono text-xs text-primary">{user.karma_score}★</span>
              </Link>
              <button
                type="button"
                onClick={logout}
                className="rounded-xl border border-border p-2 text-muted hover:text-danger"
                aria-label="Cerrar sesión"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <Link
              href="/auth/login"
              className="flex items-center gap-2 rounded-xl border border-border px-3 py-2 text-sm transition hover:border-primary/40"
            >
              <User className="h-4 w-4" />
              Ingresar
            </Link>
          )}
        </div>

        <button
          type="button"
          className="rounded-xl p-2 md:hidden"
          onClick={() => setMobileOpen(!mobileOpen)}
        >
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </nav>

      {mobileOpen && (
        <div className="glass border-t border-border px-4 py-4 md:hidden">
          {LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="block py-2 text-sm font-medium"
              onClick={() => setMobileOpen(false)}
            >
              {link.label}
            </Link>
          ))}
          <Link href={user ? "/perfil" : "/auth/login"} className="block py-2 text-sm">
            {user ? `${displayName} (${user.karma_score} karma)` : "Ingresar"}
          </Link>
          <div className="mt-3 flex items-center gap-2 border-t border-border pt-3">
            <span className="text-sm text-muted">Tema</span>
            <ThemeToggle />
          </div>
        </div>
      )}
    </header>
  );
}