"use client";
import dynamic from "next/dynamic";
import type { GeoResumen } from "@/lib/api";

// Leaflet es incompatible con SSR — carga solo en cliente
const MapaPeruInner = dynamic(() => import("./MapaPeruInner"), {
  ssr: false,
  loading: () => (
    <div className="h-96 flex items-center justify-center bg-gray-50 rounded-lg text-gray-400 text-sm">
      Cargando mapa…
    </div>
  ),
});

interface Props {
  regiones: GeoResumen[];
}

export default function MapaPeru({ regiones }: Props) {
  return (
    <div className="bg-white border rounded-xl p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">
        Distribución geográfica de procesos
        <span className="ml-2 text-xs font-normal text-gray-400">(tamaño = nº procesos)</span>
      </h3>
      <MapaPeruInner regiones={regiones} />
    </div>
  );
}
