"use client";
import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";

type Corrida = {
  id: number;
  inicio: string;
  fin: string | null;
  estado: string;
  registros_cargados: number;
  registros_nuevos: number;
  log_resumen: string | null;
};

type Estado = "idle" | "iniciando" | "ejecutando" | "listo" | "error";

export default function ActualizarDatos() {
  const [estado, setEstado] = useState<Estado>("idle");
  const [corridas, setCorridas] = useState<Corrida[]>([]);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [abierto, setAbierto] = useState(false);

  const cargarEstado = useCallback(async () => {
    try {
      const res = await api.etlEstado();
      setCorridas(res.corridas);
      // Si la última corrida estaba en "running" y terminó → notificar
      if (res.corridas.length > 0 && estado === "ejecutando") {
        const ultima = res.corridas[0];
        if (ultima.estado !== "running") {
          setEstado(ultima.estado === "success" ? "listo" : "error");
          if (ultima.estado === "success") {
            const nuevas = ultima.registros_nuevos ?? 0;
            setMensaje(
              nuevas > 0
                ? `✓ ${nuevas.toLocaleString("es-PE")} nuevas convocatorias encontradas.`
                : "✓ Datos al día, no hay convocatorias nuevas."
            );
          } else {
            setMensaje(ultima.log_resumen ?? "Error al actualizar.");
          }
        }
      }
    } catch {
      // silencioso
    }
  }, [estado]);

  // Polling cada 5 s mientras ejecuta
  useEffect(() => {
    if (estado !== "ejecutando") return;
    const timer = setInterval(cargarEstado, 5000);
    return () => clearInterval(timer);
  }, [estado, cargarEstado]);

  // Cargar historial al abrir el panel
  useEffect(() => {
    if (abierto) cargarEstado();
  }, [abierto, cargarEstado]);

  const ejecutar = async () => {
    setEstado("iniciando");
    setMensaje(null);
    try {
      const res = await api.etlEjecutar();
      if (res.status === "iniciado") {
        setEstado("ejecutando");
        setMensaje("ETL en ejecución. Puede tomar varios minutos...");
        await cargarEstado();
      } else {
        setEstado("error");
        setMensaje(res.mensaje ?? "Error al iniciar el ETL");
      }
    } catch {
      setEstado("error");
      setMensaje("No se pudo conectar con el backend.");
    }
  };

  const ESTADO_COLOR: Record<string, string> = {
    success: "text-green-600",
    error:   "text-red-500",
    running: "text-yellow-500",
  };

  const btnLabel = {
    idle:       "Actualizar Datos",
    iniciando:  "Iniciando...",
    ejecutando: "Actualizando...",
    listo:      "Actualizar Datos",
    error:      "Reintentar",
  }[estado];

  const btnDisabled = estado === "iniciando" || estado === "ejecutando";

  return (
    <div className="relative">
      <div className="flex items-center gap-2">
        <button
          onClick={ejecutar}
          disabled={btnDisabled}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
        >
          {btnDisabled ? (
            <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582M20 20v-5h-.581M5.635 15A8 8 0 1118.364 9" />
            </svg>
          )}
          {btnLabel}
        </button>

        <button
          onClick={() => setAbierto(!abierto)}
          className="text-xs text-gray-500 hover:text-gray-700 underline"
        >
          {abierto ? "Ocultar historial" : "Ver historial"}
        </button>
      </div>

      {mensaje && (
        <p className={`mt-1 text-xs ${estado === "error" ? "text-red-500" : estado === "listo" ? "text-green-600" : "text-blue-500"}`}>
          {mensaje}
        </p>
      )}

      {abierto && (
        <div className="mt-3 bg-white border rounded-xl shadow-sm p-3 text-xs w-[420px]">
          <p className="font-semibold text-gray-700 mb-2">Historial de actualizaciones</p>
          {corridas.length === 0 ? (
            <p className="text-gray-400">Sin registros.</p>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="text-gray-500 border-b">
                  <th className="text-left py-1">Inicio</th>
                  <th className="text-left py-1">Estado</th>
                  <th className="text-right py-1 text-green-600">Nuevas</th>
                  <th className="text-right py-1">Procesadas</th>
                </tr>
              </thead>
              <tbody>
                {corridas.map((c) => (
                  <tr key={c.id} className="border-b last:border-0">
                    <td className="py-1 pr-2 text-gray-600">{c.inicio?.slice(0, 16).replace("T", " ")}</td>
                    <td className={`py-1 font-medium ${ESTADO_COLOR[c.estado] ?? "text-gray-500"}`}>{c.estado}</td>
                    <td className="py-1 text-right font-semibold text-green-600">
                      {(c.registros_nuevos ?? 0) > 0 ? `+${c.registros_nuevos.toLocaleString("es-PE")}` : "—"}
                    </td>
                    <td className="py-1 text-right text-gray-600">{c.registros_cargados?.toLocaleString("es-PE") ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
