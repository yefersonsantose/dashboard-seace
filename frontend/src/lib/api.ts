// En el navegador usamos URL relativa (/api/...) para que el tráfico pase
// por el servidor Next.js (que hace proxy al backend). Así solo se necesita
// exponer 1 puerto al internet. En SSR usamos la URL directa al backend.
const BASE =
  typeof window !== "undefined"
    ? "/api"
    : (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000");

async function get<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
  const url = new URL(`${BASE}${path}`);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, String(v));
    });
  }
  const res = await fetch(url.toString(), { next: { revalidate: 60 } });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json();
}

export interface KPIs {
  total_procesos: number;
  monto_total: number | null;
  procesos_nuevos_7d: number;
  entidades_activas: number;
  ultima_actualizacion: string | null;
}

export interface Proceso {
  id: number;
  codigo_seace: string;
  entidad: string;
  objeto_contratacion: string | null;
  tipo_proceso: string | null;
  estado: string | null;
  valor_referencial: number | null;
  moneda: string | null;
  fecha_convocatoria: string | null;
  nivel_gobierno: string | null;
  departamento: string | null;
  provincia: string | null;
  url_seace: string | null;
}

export interface ProcesoDetalle extends Proceso {
  nro_expediente: string | null;
  descripcion: string | null;
  fecha_buena_pro: string | null;
  fecha_suscripcion: string | null;
  distrito: string | null;
  ubigeo: string | null;
  ingested_at: string | null;
}

export interface Paginacion {
  total: number;
  pagina: number;
  por_pagina: number;
  paginas: number;
}

export interface ProcesosPaginados {
  data: Proceso[];
  paginacion: Paginacion;
}

export interface GeoResumen {
  ubigeo: string;
  nombre: string;
  total_procesos: number;
  monto_total: number | null;
}

export interface Catalogo {
  codigo: string;
  nombre: string;
}

export interface AnalyticsItem {
  nombre: string;
  total_procesos: number;
  monto_total: number | null;
}

export interface MesItem {
  periodo: string;
  total_procesos: number;
  monto_total: number | null;
}

export const api = {
  kpis: () => get<KPIs>("/kpis"),
  procesos: (params?: Record<string, string | number | undefined>) =>
    get<ProcesosPaginados>("/procesos", params),
  proceso: (codigo: string) => get<ProcesoDetalle>(`/procesos/${codigo}`),
  geoRegiones: () => get<GeoResumen[]>("/geo/regiones"),
  analyticsPorEstado: () => get<AnalyticsItem[]>("/analytics/por-estado"),
  analyticsPorMes: () => get<MesItem[]>("/analytics/por-mes"),
  analyticsTopEntidades: () => get<AnalyticsItem[]>("/analytics/top-entidades"),
  analyticsPorTipo: () => get<AnalyticsItem[]>("/analytics/por-tipo"),
  analyticsPorNivel: () => get<AnalyticsItem[]>("/analytics/por-nivel"),
  estados: () => get<Catalogo[]>("/catalogos/estados"),
  tiposProceso: () => get<Catalogo[]>("/catalogos/tipos-proceso"),
  regiones: () => get<Catalogo[]>("/catalogos/regiones"),
  nivelesGobierno: () => get<Catalogo[]>("/catalogos/niveles-gobierno"),
};
