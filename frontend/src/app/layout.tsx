import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Dashboard SEACE",
  description: "Seguimiento de procesos de contratación pública del SEACE",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className={inter.className}>
        <header className="bg-brand text-white shadow-md">
          <div className="max-w-7xl mx-auto px-4 py-3 flex items-center gap-3">
            <div className="font-bold text-lg tracking-tight">SEACE Dashboard</div>
            <span className="text-blue-200 text-sm">| Contrataciones Públicas del Perú</span>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-4 py-6">{children}</main>
      </body>
    </html>
  );
}
