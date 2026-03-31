"use client";
import { useEffect, useState, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import type { KPIs, Proceso, Paginacion, Catalogo, AnalyticsItem, MesItem, GeoResumen } from "@/lib/api";
import KPICards from "@/components/KPICards";
import FilterPanel, { type Filtros } from "@/components/FilterPanel";
import ProcessTable from "@/components/ProcessTable";
import { TendenciaMensual, GraficoPorEstado, TopEntidades, GraficoPorTipo, GraficoPorNivel } from "@/components/Charts";
import MapaPeru from "@/components/MapaPeru";

type Tab = "tabla" | "analitica" | "mapa";

export default function Home() {
  return (
    <Suspense>
      <HomeInner />
    </Suspense>
  );
}

function HomeInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [tab, setTab] = useState<Tab>("tabla");

  // ── Datos KPI y catálogos ──────────────────────────────────
  const [kpis, setKpis] = useState<KPIs | null>(null);
  const [estados, setEstados] = useState<Catalogo[]>([]);
  const [tipos, setTipos] = useState<Catalogo[]>([]);
  const [loadingKpis, setLoadingKpis] = useState(true);

  // ── Tabla ──────────────────────────────────────────────────
  const [procesos, setProcesos] = useState<Proceso[]>([]);
  const [paginacion, setPaginacion] = useState<Paginacion | null>(null);

  // Inicializar filtros desde URL params (para compartir enlaces)
  const [filtros, setFiltros] = useState<Filtros>(() => ({
    texto:       searchParams.get("texto")       ?? undefined,
    estado:      searchParams.get("estado")      ?? undefined,
    tipo:        searchParams.get("tipo")         ?? undefined,
    nivel:       searchParams.get("nivel")        ?? undefined,
    departamento:searchParams.get("departamento") ?? undefined,
    provincia:   searchParams.get("provincia")    ?? undefined,
    fecha_desde: searchParams.get("fecha_desde")  ?? undefined,
    fecha_hasta: searchParams.get("fecha_hasta")  ?? undefined,
    monto_min:   searchParams.get("monto_min")    ?? undefined,
    monto_max:   searchParams.get("monto_max")    ?? undefined,
  }));
  const [pagina, setPagina] = useState(() => Number(searchParams.get("pagina") ?? 1));
  const [loadingTabla, setLoadingTabla] = useState(true);
  const [errorTabla, setErrorTabla] = useState<string | null>(null);

  // ── Analítica ──────────────────────────────────────────────
  const [porEstado, setPorEstado] = useState<AnalyticsItem[]>([]);
  const [porMes, setPorMes] = useState<MesItem[]>([]);
  const [topEntidades, setTopEntidades] = useState<AnalyticsItem[]>([]);
  const [porTipo, setPorTipo] = useState<AnalyticsItem[]>([]);
  const [porNivel, setPorNivel] = useState<AnalyticsItem[]>([]);
  const [loadingAnalitica, setLoadingAnalitica] = useState(false);
  const [analiticaCargada, setAnaliticaCargada] = useState(false);

  // ── Mapa ───────────────────────────────────────────────────
  const [regiones, setRegiones] = useState<GeoResumen[]>([]);
  const [loadingMapa, setLoadingMapa] = useState(false);
  const [mapaCargado, setMapaCargado] = useState(false);

  // ── Carga inicial ──────────────────────────────────────────
  useEffect(() => {
    api.kpis().then(setKpis).catch(() => {}).finally(() => setLoadingKpis(false));
    api.estados().then(setEstados).catch(() => {});
    api.tiposProceso().then(setTipos).catch(() => {});
  }, []);

  const cargarProcesos = useCallback(async (f: Filtros, p: number) => {
    setLoadingTabla(true);
    setErrorTabla(null);
    try {
      const res = await api.procesos({
        texto: f.texto, estado: f.estado, tipo: f.tipo,
        nivel: f.nivel, departamento: f.departamento, provincia: f.provincia,
        fecha_desde: f.fecha_desde, fecha_hasta: f.fecha_hasta,
        monto_min: f.monto_min ? Number(f.monto_min) : undefined,
        monto_max: f.monto_max ? Number(f.monto_max) : undefined,
        pagina: p, por_pagina: 50,
      });
      setProcesos(res.data);
      setPaginacion(res.paginacion);
    } catch {
      setErrorTabla("No se pudo conectar con la API. Verifica que el backend esté activo.");
    } finally {
      setLoadingTabla(false);
    }
  }, []);

  useEffect(() => { cargarProcesos(filtros, pagina); }, [filtros, pagina, cargarProcesos]);

  // Lazy-load analítica y mapa al cambiar de tab
  useEffect(() => {
    if (tab === "analitica" && !analiticaCargada) {
      setLoadingAnalitica(true);
      Promise.all([
        api.analyticsPorEstado(),
        api.analyticsPorMes(),
        api.analyticsTopEntidades(),
        api.analyticsPorTipo(),
        api.analyticsPorNivel(),
      ]).then(([estado, mes, top, tipo, nivel]) => {
        setPorEstado(estado);
        setPorMes(mes);
        setTopEntidades(top);
        setPorTipo(tipo);
        setPorNivel(nivel);
        setAnaliticaCargada(true);
      }).catch(() => {}).finally(() => setLoadingAnalitica(false));
    }
    if (tab === "mapa" && !mapaCargado) {
      setLoadingMapa(true);
      api.geoRegiones().then((r) => { setRegiones(r); setMapaCargado(true); })
        .catch(() => {}).finally(() => setLoadingMapa(false));
    }
  }, [tab, analiticaCargada, mapaCargado]);

  function handleFiltros(f: Filtros) {
    setFiltros(f);
    setPagina(1);
    // Actualizar URL para que el enlace sea compartible
    const params = new URLSearchParams();
    Object.entries(f).forEach(([k, v]) => { if (v) params.set(k, v); });
    router.replace(`/?${params.toString()}`, { scroll: false });
  }

  const tabClass = (t: Tab) =>
    `px-4 py-2 text-sm font-medium rounded-t-lg border-b-2 transition-colors ${
      tab === t
        ? "border-brand text-brand bg-white"
        : "border-transparent text-gray-500 hover:text-gray-700"
    }`;

  return (
    <div>
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-gray-800">Procesos de Contratación</h1>
        <p className="text-sm text-gray-500">Fuente: SEACE — Sistema Electrónico de Contrataciones del Estado</p>
      </div>

      <KPICards kpis={kpis} loading={loadingKpis} />

      {/* Tabs */}
      <div className="flex gap-1 border-b mb-0 mt-2">
        <button className={tabClass("tabla")} onClick={() => setTab("tabla")}>Tabla de procesos</button>
        <button className={tabClass("analitica")} onClick={() => setTab("analitica")}>Analítica</button>
        <button className={tabClass("mapa")} onClick={() => setTab("mapa")}>Mapa</button>
      </div>

      {/* ── Tab: Tabla ── */}
      {tab === "tabla" && (
        <div className="mt-4">
          <FilterPanel estados={estados} tipos={tipos} initialFiltros={filtros} onChange={handleFiltros} />
          {errorTabla && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-4 mb-4 text-sm">{errorTabla}</div>
          )}
          <ProcessTable
            data={procesos}
            paginacion={paginacion}
            loading={loadingTabla}
            onPage={setPagina}
            filtros={{
              texto: filtros.texto, estado: filtros.estado, tipo: filtros.tipo,
              nivel: filtros.nivel, departamento: filtros.departamento, provincia: filtros.provincia,
              fecha_desde: filtros.fecha_desde, fecha_hasta: filtros.fecha_hasta,
              monto_min: filtros.monto_min ? Number(filtros.monto_min) : undefined,
              monto_max: filtros.monto_max ? Number(filtros.monto_max) : undefined,
            }}
          />
        </div>
      )}

      {/* ── Tab: Analítica ── */}
      {tab === "analitica" && (
        <div className="mt-4">
          {loadingAnalitica ? (
            <div className="text-center py-16 text-gray-400">Cargando analítica…</div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="lg:col-span-2"><TendenciaMensual data={porMes} /></div>
              <GraficoPorNivel data={porNivel} />
              <GraficoPorEstado data={porEstado} />
              <GraficoPorTipo data={porTipo} />
              <div className="lg:col-span-2"><TopEntidades data={topEntidades} /></div>
            </div>
          )}
        </div>
      )}

      {/* ── Tab: Mapa ── */}
      {tab === "mapa" && (
        <div className="mt-4">
          {loadingMapa ? (
            <div className="text-center py-16 text-gray-400">Cargando mapa…</div>
          ) : (
            <MapaPeru regiones={regiones} />
          )}
        </div>
      )}
    </div>
  );
}

