import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// During development, /api and /health are proxied to the FastAPI backend so the
// frontend can use same-origin relative URLs. Override the target with BACKEND_URL.
const backend = process.env.BACKEND_URL || "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: Number(process.env.FRONTEND_PORT) || 5173,
    proxy: {
      "/api": { target: backend, changeOrigin: true },
      "/health": { target: backend, changeOrigin: true },
    },
  },
});
