import { api } from "@/lib/api";
import Link from "next/link";

function fmtMonto(n: number | null, moneda: string | null) {
  if (!n) return "—";
  return new Intl.NumberFormat("es-PE", { style: "currency", currency: moneda ?? "PEN" }).format(n);
}

function Row({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div className="flex flex-col sm:flex-row sm:gap-4 py-3 border-b last:border-0">
      <span className="text-xs text-gray-500 uppercase tracking-wide w-48 shrink-0">{label}</span>
      <span className="text-sm text-gray-800 break-words">{value ?? "—"}</span>
    </div>
  );
}

export default async function DetalleProceso({ params }: { params: { codigo: string } }) {
  let proceso = null;
  let err = null;
  try {
    proceso = await api.proceso(params.codigo);
  } catch {
    err = "Proceso no encontrado o API no disponible.";
  }

  return (
    <div>
      <Link href="/" className="text-blue-600 text-sm hover:underline mb-4 inline-block">← Volver al listado</Link>
      {err ? (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-6">{err}</div>
      ) : proceso ? (
        <div className="bg-white border rounded-xl p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-1">{proceso.codigo_seace}</h2>
          <p className="text-sm text-gray-500 mb-6">{proceso.entidad}</p>
          <Row label="Expediente" value={proceso.nro_expediente} />
          <Row label="Objeto" value={proceso.objeto_contratacion} />
          <Row label="Descripción" value={proceso.descripcion} />
          <Row label="Tipo de proceso" value={proceso.tipo_proceso} />
          <Row label="Estado" value={proceso.estado} />
          <Row label="Valor referencial" value={fmtMonto(proceso.valor_referencial, proceso.moneda)} />
          <Row label="Fecha convocatoria" value={proceso.fecha_convocatoria} />
          <Row label="Fecha buena pro" value={proceso.fecha_buena_pro} />
          <Row label="Fecha suscripción" value={proceso.fecha_suscripcion} />
          <Row label="Nivel de gobierno" value={proceso.nivel_gobierno} />
          <Row label="Departamento" value={proceso.departamento} />
          <Row label="Provincia" value={proceso.provincia} />
          <Row label="Distrito" value={proceso.distrito} />
          <Row label="Ubigeo" value={proceso.ubigeo} />
          {proceso.url_seace && (
            <div className="py-3">
              <span className="text-xs text-gray-500 uppercase tracking-wide">Fuente SEACE</span>
              <a href={proceso.url_seace} target="_blank" rel="noopener noreferrer" className="block text-sm text-blue-600 hover:underline break-all mt-1">
                {proceso.url_seace}
              </a>
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}
