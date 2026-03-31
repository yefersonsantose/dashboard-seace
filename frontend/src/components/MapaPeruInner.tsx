"use client";
import { useEffect, useRef } from "react";
import type { GeoResumen } from "@/lib/api";

interface Props {
  regiones: GeoResumen[];
}

// GeoJSON simplificado de regiones del Perú (centroides para marcadores)
const CENTROIDES: Record<string, [number, number]> = {
  "01": [-6.77, -79.84],   // Amazonas
  "02": [-9.53, -77.53],   // Áncash
  "03": [-13.16, -74.22],  // Apurímac
  "04": [-13.85, -72.52],  // Arequipa — aprox
  "05": [-14.07, -75.74],  // Ayacucho
  "06": [-7.17, -78.51],   // Cajamarca
  "07": [-12.05, -77.04],  // Callao
  "08": [-12.86, -74.93],  // Cusco — aprox
  "09": [-9.91, -76.24],   // Huánuco
  "10": [-13.79, -76.11],  // Ica
  "11": [-11.16, -75.99],  // Junín
  "12": [-6.77, -79.84],   // La Libertad — aprox
  "13": [-6.77, -79.84],   // Lambayeque — aprox
  "14": [-12.05, -77.04],  // Lima
  "15": [-3.75, -73.25],   // Loreto
  "16": [-8.39, -74.53],   // Madre de Dios
  "17": [-14.84, -70.02],  // Moquegua
  "18": [-10.67, -75.23],  // Pasco
  "19": [-5.20, -80.62],   // Piura
  "20": [-15.84, -70.02],  // Puno
  "21": [-6.05, -76.97],   // San Martín
  "22": [-18.01, -70.25],  // Tacna
  "23": [-4.57, -81.27],   // Tumbes
  "24": [-8.38, -74.54],   // Ucayali
};

// Mapa de nombre de región → código
const NOMBRE_CODIGO: Record<string, string> = {
  "AMAZONAS": "01", "ANCASH": "02", "ÁPURÍMAC": "03", "APURIMAC": "03",
  "AREQUIPA": "04", "AYACUCHO": "05", "CAJAMARCA": "06", "CALLAO": "07",
  "CUSCO": "08", "CUZCO": "08", "HUÁNUCO": "09", "HUANUCO": "09",
  "ICA": "10", "JUNÍN": "11", "JUNIN": "11", "LA LIBERTAD": "12",
  "LAMBAYEQUE": "13", "LIMA": "14", "LORETO": "15", "MADRE DE DIOS": "16",
  "MOQUEGUA": "17", "PASCO": "18", "PIURA": "19", "PUNO": "20",
  "SAN MARTÍN": "21", "SAN MARTIN": "21", "TACNA": "22", "TUMBES": "23",
  "UCAYALI": "24",
};

function getColor(total: number, max: number): string {
  const t = max > 0 ? total / max : 0;
  if (t > 0.75) return "#1a4b8c";
  if (t > 0.5) return "#2563eb";
  if (t > 0.25) return "#60a5fa";
  return "#bfdbfe";
}

export default function MapaPeruInner({ regiones }: Props) {
  const mapRef = useRef<any>(null);
  const divRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!divRef.current || mapRef.current) return;

    // Importar Leaflet dinámicamente (solo cliente)
    import("leaflet").then((L) => {
      // Fix icono default en webpack
      delete (L.Icon.Default.prototype as any)._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
        iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
        shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
      });

      const map = L.map(divRef.current!, {
        center: [-9.19, -75.0],
        zoom: 5,
        zoomControl: true,
        attributionControl: true,
      });
      mapRef.current = map;

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "© OpenStreetMap contributors",
        maxZoom: 10,
      }).addTo(map);

      if (regiones.length === 0) {
        // Marcador de ejemplo cuando no hay datos de regiones
        L.marker([-12.05, -77.04])
          .addTo(map)
          .bindPopup("<b>Lima</b><br/>Sin datos de región aún");
        return;
      }

      const max = Math.max(...regiones.map((r) => r.total_procesos));

      regiones.forEach((region) => {
        const codigo = NOMBRE_CODIGO[region.nombre.toUpperCase()];
        const coords = codigo ? CENTROIDES[codigo] : null;
        if (!coords) return;

        const radio = 8 + (region.total_procesos / max) * 22;
        const color = getColor(region.total_procesos, max);

        L.circleMarker(coords, {
          radius: radio,
          fillColor: color,
          color: "#fff",
          weight: 1.5,
          opacity: 1,
          fillOpacity: 0.8,
        })
          .addTo(map)
          .bindPopup(
            `<b>${region.nombre}</b><br/>` +
            `Procesos: <b>${region.total_procesos.toLocaleString("es-PE")}</b><br/>` +
            `Monto: <b>S/ ${region.monto_total ? (region.monto_total / 1_000_000).toFixed(1) + "M" : "—"}</b>`
          );
      });
    });

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, [regiones]);

  return (
    <>
      <link
        rel="stylesheet"
        href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
      />
      <div ref={divRef} style={{ height: "380px", width: "100%", borderRadius: "8px" }} />
    </>
  );
}
