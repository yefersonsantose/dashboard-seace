"use client";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, Legend,
} from "recharts";
import type { AnalyticsItem, MesItem } from "@/lib/api";

const COLORS = ["#1a4b8c", "#2563eb", "#3b82f6", "#60a5fa", "#93c5fd", "#bfdbfe", "#1d4ed8", "#1e40af"];

function fmtMonto(n: number | null) {
  if (!n) return "—";
  if (n >= 1_000_000_000) return `S/ ${(n / 1_000_000_000).toFixed(1)}B`;
  if (n >= 1_000_000) return `S/ ${(n / 1_000_000).toFixed(1)}M`;
  return `S/ ${n.toLocaleString("es-PE", { maximumFractionDigits: 0 })}`;
}

function fmtMes(periodo: string) {
  const [y, m] = periodo.split("-");
  const meses = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"];
  return `${meses[parseInt(m) - 1]} ${y}`;
}

// ── Tendencia mensual ──────────────────────────────────────────

interface TendenciaProps { data: MesItem[] }

export function TendenciaMensual({ data }: TendenciaProps) {
  const transformed = data.map((d) => ({
    ...d,
    label: fmtMes(d.periodo),
    monto_M: d.monto_total ? d.monto_total / 1_000_000 : 0,
  }));
  return (
    <div className="bg-white border rounded-xl p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Tendencia mensual de procesos</h3>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={transformed} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="label" tick={{ fontSize: 11 }} />
          <YAxis yAxisId="left" tick={{ fontSize: 11 }} />
          <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} tickFormatter={(v) => `${v.toFixed(0)}M`} />
          <Tooltip
            formatter={(value: number, name: string) =>
              name === "Procesos" ? [value, name] : [`S/ ${value.toFixed(1)}M`, "Monto"]
            }
          />
          <Legend />
          <Bar yAxisId="left" dataKey="total_procesos" name="Procesos" fill="#bfdbfe" radius={[4, 4, 0, 0]} />
          <Line yAxisId="right" type="monotone" dataKey="monto_M" name="Monto (M)" stroke="#1a4b8c" strokeWidth={2} dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── Por estado (pie) ───────────────────────────────────────────

interface EstadoProps { data: AnalyticsItem[] }

export function GraficoPorEstado({ data }: EstadoProps) {
  return (
    <div className="bg-white border rounded-xl p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Distribución por estado</h3>
      <ResponsiveContainer width="100%" height={220}>
        <PieChart>
          <Pie
            data={data}
            dataKey="total_procesos"
            nameKey="nombre"
            cx="50%"
            cy="50%"
            outerRadius={80}
            label={({ nombre, percent }) => `${nombre} ${(percent * 100).toFixed(0)}%`}
            labelLine={false}
          >
            {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
          </Pie>
          <Tooltip formatter={(v: number) => [v.toLocaleString("es-PE"), "Procesos"]} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── Top entidades (barra horizontal) ─────────────────────────

interface TopProps { data: AnalyticsItem[] }

export function TopEntidades({ data }: TopProps) {
  const top = data.slice(0, 8).map((d) => ({
    ...d,
    nombre_corto: d.nombre.length > 35 ? d.nombre.slice(0, 35) + "…" : d.nombre,
    monto_M: d.monto_total ? d.monto_total / 1_000_000 : 0,
  }));
  return (
    <div className="bg-white border rounded-xl p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Top entidades por monto contratado</h3>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={top} layout="vertical" margin={{ top: 0, right: 60, left: 10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f0f0f0" />
          <XAxis type="number" tick={{ fontSize: 10 }} tickFormatter={(v) => `${v.toFixed(0)}M`} />
          <YAxis type="category" dataKey="nombre_corto" tick={{ fontSize: 10 }} width={200} />
          <Tooltip formatter={(v: number) => [`S/ ${v.toFixed(1)}M`, "Monto"]} />
          <Bar dataKey="monto_M" fill="#2563eb" radius={[0, 4, 4, 0]}>
            {top.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── Por nivel de gobierno ──────────────────────────────────────

const NIVEL_COLORS: Record<string, string> = {
  "Gobierno Nacional":    "#7c3aed",
  "Gobierno Regional":    "#059669",
  "Municipal Provincial": "#d97706",
  "Municipal Distrital":  "#ca8a04",
};

export function GraficoPorNivel({ data }: EstadoProps) {
  const colored = data.map((d) => ({ ...d, fill: NIVEL_COLORS[d.nombre] ?? "#6b7280" }));
  return (
    <div className="bg-white border rounded-xl p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Procesos por nivel de gobierno</h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={colored} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="nombre" tick={{ fontSize: 10 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip
            formatter={(v: number, name: string) =>
              name === "Procesos" ? [v.toLocaleString("es-PE"), name] : [v, name]
            }
          />
          <Bar dataKey="total_procesos" name="Procesos" radius={[4, 4, 0, 0]}>
            {colored.map((d, i) => <Cell key={i} fill={d.fill} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}


// ── Por tipo de proceso ────────────────────────────────────────

export function GraficoPorTipo({ data }: EstadoProps) {
  return (
    <div className="bg-white border rounded-xl p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Procesos por tipo</h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="nombre" tick={{ fontSize: 10, angle: -35, textAnchor: "end" } as object} interval={0} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          <Bar dataKey="total_procesos" name="Procesos" radius={[4, 4, 0, 0]}>
            {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
