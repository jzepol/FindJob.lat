"use client";

import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { SalaryRole, Seniority } from "@/lib/types";
import { seniorityLabel } from "@/lib/utils";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export default function SalariosPage() {
  const [roles, setRoles] = useState<SalaryRole[]>([]);
  const [seniority, setSeniority] = useState<Seniority | "">("");
  const [location, setLocation] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const params = new URLSearchParams();
    if (seniority) params.set("seniority", seniority);
    if (location) params.set("location", location);

    setLoading(true);
    fetch(`${API_BASE}/salaries?${params}`)
      .then((r) => r.json())
      .then((data: SalaryRole[]) => setRoles(data))
      .catch(() => setRoles([]))
      .finally(() => setLoading(false));
  }, [seniority, location]);

  const chartData = roles.slice(0, 8).map((r) => ({
    name: r.role.length > 22 ? `${r.role.slice(0, 22)}…` : r.role,
    promedio: r.salary_avg ? Number(r.salary_avg) : 0,
    min: r.salary_min ? Number(r.salary_min) : 0,
    max: r.salary_max ? Number(r.salary_max) : 0,
  }));

  const fmt = (n: number) =>
    new Intl.NumberFormat("es-AR", { notation: "compact", maximumFractionDigits: 1 }).format(n);

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="font-display text-3xl font-bold">Salarios en LATAM</h1>
        <p className="mt-1 text-muted">
          Rangos agregados desde ofertas reales scrapeadas
        </p>
      </div>

      <div className="mb-8 flex flex-wrap gap-4">
        <select
          value={seniority}
          onChange={(e) => setSeniority(e.target.value as Seniority | "")}
          className="glass rounded-xl px-4 py-2.5 text-sm outline-none"
        >
          <option value="">Todos los niveles</option>
          {(["junior", "mid", "senior", "lead"] as Seniority[]).map((s) => (
            <option key={s} value={s}>
              {seniorityLabel(s)}
            </option>
          ))}
        </select>
        <input
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          placeholder="Filtrar por provincia/ciudad"
          className="glass min-w-[220px] rounded-xl px-4 py-2.5 text-sm outline-none"
        />
      </div>

      {chartData.length > 0 && (
        <div className="glass mb-10 rounded-2xl p-6">
          <h2 className="mb-6 font-display text-lg font-semibold">
            Promedio por rol
          </h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 16 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis
                  type="number"
                  tick={{ fill: "var(--muted)", fontSize: 11 }}
                  tickFormatter={fmt}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={140}
                  tick={{ fill: "var(--muted)", fontSize: 11 }}
                />
                <Tooltip
                  contentStyle={{
                    background: "var(--surface)",
                    border: "1px solid var(--border)",
                    borderRadius: 12,
                    color: "var(--foreground)",
                  }}
                  formatter={(v) => [fmt(Number(v ?? 0)), "Promedio"]}
                />
                <Bar dataKey="promedio" fill="#14B8A6" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="skeleton h-36 rounded-2xl" />
          ))}
        </div>
      ) : roles.length === 0 ? (
        <div className="glass rounded-2xl p-12 text-center text-muted">
          No hay datos salariales con los filtros actuales.
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {roles.map((role) => (
            <div key={`${role.role}-${role.seniority}`} className="glass card-hover rounded-2xl p-5">
              <h3 className="font-display font-semibold leading-snug">{role.role}</h3>
              <p className="mt-1 text-xs text-muted">
                {seniorityLabel(role.seniority)} · {role.count} ofertas
              </p>
              <div className="mt-4 space-y-1 font-mono text-sm">
                {role.salary_min && (
                  <p>
                    <span className="text-muted">Min </span>
                    <span className="text-accent">
                      {role.currency} {Number(role.salary_min).toLocaleString("es-AR")}
                    </span>
                  </p>
                )}
                {role.salary_avg && (
                  <p>
                    <span className="text-muted">Avg </span>
                    <span className="text-primary">
                      {role.currency} {Number(role.salary_avg).toLocaleString("es-AR")}
                    </span>
                  </p>
                )}
                {role.salary_max && (
                  <p>
                    <span className="text-muted">Max </span>
                    <span className="text-foreground">
                      {role.currency} {Number(role.salary_max).toLocaleString("es-AR")}
                    </span>
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}