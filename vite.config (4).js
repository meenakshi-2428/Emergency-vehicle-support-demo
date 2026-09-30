import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      manifest: {
        name: "GeoAgentic Driver & Civilian App",
        short_name: "GeoAgentic",
        theme_color: "#1f1a5e",
        background_color: "#0b1020",
        display: "standalone",
        icons: [],
      },
    }),
  ],
});
