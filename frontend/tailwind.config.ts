import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        brand: { DEFAULT: "#1a4b8c", light: "#2563eb", dark: "#0f2d57" },
      },
    },
  },
  plugins: [],
};
export default config;
