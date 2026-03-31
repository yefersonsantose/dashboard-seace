"use client";
import type { Proceso, Paginacion } from "@/lib/api";
import Link from "next/link";

const NIVEL_COLORS: Record<string, string> = {
  "Gobierno Nacional":    "bg-purple-100 text-purple-700",
  "Gobierno Regional":    "bg-green-100 text-green-700",
  "Municipal Provincial": "bg-orange-100 text-orange-700",
  "Municipal Distrital":  "bg-yellow-100 text-yellow-700",
};

function NivelBadge({ nivel }: { nivel: string | null }) {
  if (!nivel) return <span className="text-gray-400">—</span>;
  const cls = NIVEL_COLORS[nivel] ?? "bg-gray-100 text-gray-600";
  const short = nivel.replace("Gobierno ", "").replace("Municipal ", "Mun. ");
  return <span className={`rounded px-2 py-0.5 text-xs font-medium ${cls}`}>{short}</span>;
}

interface Props {
  data: Proceso[];
  paginacion: Paginacion | null;
  loading?: boolean;
  onPage: (p: number) => void;
}

function fmtMonto(n: number | null, moneda: string | null) {
  if (!n) return "—";
  return new Intl.NumberFormat("es-PE", { style: "currency", currency: moneda ?? "PEN", maximumFractionDigits: 0 }).format(n);
}

export default function ProcessTable({ data, paginacion, loading, onPage }: Props) {
  return (
    <div className="bg-white border rounded-xl overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-100 text-gray-600 uppercase text-xs">
            <tr>
              <th className="px-3 py-3 text-left">Código SEACE</th>
              <th className="px-3 py-3 text-left">Entidad</th>
              <th className="px-3 py-3 text-left">Objeto</th>
              <th className="px-3 py-3 text-left">Tipo</th>
              <th className="px-3 py-3 text-left">Estado</th>
              <th className="px-3 py-3 text-right">Monto</th>
              <th className="px-3 py-3 text-left">Convocatoria</th>
              <th className="px-3 py-3 text-left">Nivel</th>
              <th className="px-3 py-3 text-left">Departamento</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={9} className="text-center py-10 text-gray-400">Cargando...</td></tr>
            ) : data.length === 0 ? (
              <tr><td colSpan={9} className="text-center py-10 text-gray-400">Sin resultados</td></tr>
            ) : (
              data.map((p) => (
                <tr key={p.id} className="border-t hover:bg-gray-50">
                  <td className="px-3 py-2 font-mono text-xs">
                    <Link href={`/proceso/${p.codigo_seace}`} className="text-blue-600 hover:underline">{p.codigo_seace}</Link>
                  </td>
                  <td className="px-3 py-2 max-w-[180px] truncate">{p.entidad}</td>
                  <td className="px-3 py-2 max-w-[320px] break-words whitespace-normal leading-snug">{p.objeto_contratacion ?? "—"}</td>
                  <td className="px-3 py-2 text-xs">{p.tipo_proceso ?? "—"}</td>
                  <td className="px-3 py-2">
                    <span className="bg-blue-100 text-blue-700 rounded px-2 py-0.5 text-xs">{p.estado ?? "—"}</span>
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-xs">{fmtMonto(p.valor_referencial, p.moneda)}</td>
                  <td className="px-3 py-2 text-xs">{p.fecha_convocatoria ?? "—"}</td>
                  <td className="px-3 py-2 text-xs">
                    <NivelBadge nivel={p.nivel_gobierno} />
                  </td>
                  <td className="px-3 py-2 text-xs">{p.departamento ?? "—"}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      {paginacion && paginacion.paginas > 1 && (
        <div className="flex items-center justify-between px-4 py-3 border-t text-sm text-gray-600">
          <span>{paginacion.total.toLocaleString("es-PE")} resultados</span>
          <div className="flex gap-2">
            <button disabled={paginacion.pagina <= 1} onClick={() => onPage(paginacion.pagina - 1)} className="px-3 py-1 border rounded disabled:opacity-40">← Anterior</button>
            <span className="px-3 py-1">{paginacion.pagina} / {paginacion.paginas}</span>
            <button disabled={paginacion.pagina >= paginacion.paginas} onClick={() => onPage(paginacion.pagina + 1)} className="px-3 py-1 border rounded disabled:opacity-40">Siguiente →</button>
          </div>
        </div>
      )}
    </div>
  );
}
