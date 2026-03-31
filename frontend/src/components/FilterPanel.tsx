"use client";
import { useState } from "react";
import type { Catalogo } from "@/lib/api";

export interface Filtros {
  texto?: string;
  estado?: string;
  tipo?: string;
  nivel?: string;
  departamento?: string;
  provincia?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
  monto_min?: string;
  monto_max?: string;
}

const NIVELES: Catalogo[] = [
  { codigo: "Gobierno Nacional",    nombre: "Gobierno Nacional" },
  { codigo: "Gobierno Regional",    nombre: "Gobierno Regional" },
  { codigo: "Municipal Provincial", nombre: "Municipal Provincial" },
  { codigo: "Municipal Distrital",  nombre: "Municipal Distrital" },
];

interface Props {
  estados: Catalogo[];
  tipos: Catalogo[];
  initialFiltros?: Filtros;
  onChange: (f: Filtros) => void;
}

export default function FilterPanel({ estados, tipos, initialFiltros, onChange }: Props) {
  const [f, setF] = useState<Filtros>(initialFiltros ?? {});
  const [copied, setCopied] = useState(false);

  function copiarEnlace() {
    navigator.clipboard.writeText(window.location.href).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  function update(key: keyof Filtros, value: string) {
    const next = { ...f, [key]: value || undefined };
    setF(next);
    onChange(next);
  }

  return (
    <div className="bg-white border rounded-xl p-4 mb-6 space-y-3">
      {/* Fila 1: búsqueda + estado + tipo + nivel */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <input
          className="border rounded px-3 py-2 text-sm lg:col-span-2"
          placeholder="Buscar por objeto de contratación..."
          value={f.texto ?? ""}
          onChange={(e) => update("texto", e.target.value)}
        />
        <select className="border rounded px-3 py-2 text-sm" value={f.estado ?? ""} onChange={(e) => update("estado", e.target.value)}>
          <option value="">Todos los estados</option>
          {estados.map((e) => <option key={e.codigo} value={e.codigo}>{e.nombre}</option>)}
        </select>
        <select className="border rounded px-3 py-2 text-sm" value={f.tipo ?? ""} onChange={(e) => update("tipo", e.target.value)}>
          <option value="">Todos los tipos</option>
          {tipos.map((t) => <option key={t.codigo} value={t.codigo}>{t.nombre}</option>)}
        </select>
      </div>
      {/* Fila 2: nivel de gobierno + departamento + provincia */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <select className="border rounded px-3 py-2 text-sm" value={f.nivel ?? ""} onChange={(e) => update("nivel", e.target.value)}>
          <option value="">Todos los niveles de gobierno</option>
          {NIVELES.map((n) => <option key={n.codigo} value={n.codigo}>{n.nombre}</option>)}
        </select>
        <input
          className="border rounded px-3 py-2 text-sm"
          placeholder="Departamento (ej. LIMA)"
          value={f.departamento ?? ""}
          onChange={(e) => update("departamento", e.target.value.toUpperCase())}
        />
        <input
          className="border rounded px-3 py-2 text-sm"
          placeholder="Provincia (ej. CUSCO)"
          value={f.provincia ?? ""}
          onChange={(e) => update("provincia", e.target.value.toUpperCase())}
        />
      </div>
      {/* Fila 3: fechas + montos + copiar enlace */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 items-center">
        <input type="date" className="border rounded px-3 py-2 text-sm" value={f.fecha_desde ?? ""} onChange={(e) => update("fecha_desde", e.target.value)} />
        <input type="date" className="border rounded px-3 py-2 text-sm" value={f.fecha_hasta ?? ""} onChange={(e) => update("fecha_hasta", e.target.value)} />
        <input type="number" className="border rounded px-3 py-2 text-sm" placeholder="Monto mín. (PEN)" value={f.monto_min ?? ""} onChange={(e) => update("monto_min", e.target.value)} />
        <input type="number" className="border rounded px-3 py-2 text-sm" placeholder="Monto máx. (PEN)" value={f.monto_max ?? ""} onChange={(e) => update("monto_max", e.target.value)} />
        <button
          onClick={copiarEnlace}
          className="border rounded px-3 py-2 text-sm font-medium transition-colors bg-white hover:bg-blue-50 border-blue-200 text-blue-700 flex items-center gap-1.5 justify-center"
          title="Copiar enlace con los filtros actuales para compartir"
        >
          {copied ? "✓ Copiado" : "🔗 Compartir"}
        </button>
      </div>
    </div>
  );
}
