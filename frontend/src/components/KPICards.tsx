"use client";
import type { KPIs } from "@/lib/api";

function fmt(n: number | null) {
  if (n === null || n === undefined) return "—";
  return new Intl.NumberFormat("es-PE").format(n);
}

function fmtMonto(n: number | null) {
  if (n === null || n === undefined) return "—";
  return new Intl.NumberFormat("es-PE", { style: "currency", currency: "PEN", maximumFractionDigits: 0 }).format(n);
}

interface Props { kpis: KPIs | null; loading?: boolean }

export default function KPICards({ kpis, loading }: Props) {
  const cards = [
    { label: "Total procesos", value: fmt(kpis?.total_procesos ?? null), color: "bg-blue-50 border-blue-200" },
    { label: "Monto total (PEN)", value: fmtMonto(kpis?.monto_total ?? null), color: "bg-green-50 border-green-200" },
    { label: "Nuevos (7 días)", value: fmt(kpis?.procesos_nuevos_7d ?? null), color: "bg-yellow-50 border-yellow-200" },
    { label: "Entidades activas", value: fmt(kpis?.entidades_activas ?? null), color: "bg-purple-50 border-purple-200" },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      {cards.map((c) => (
        <div key={c.label} className={`border rounded-xl p-4 ${c.color}`}>
          <p className="text-xs text-gray-500 uppercase tracking-wide">{c.label}</p>
          <p className="text-2xl font-bold mt-1">{loading ? "..." : c.value}</p>
        </div>
      ))}
    </div>
  );
}
