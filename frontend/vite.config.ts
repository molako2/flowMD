import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Le build est écrit dans le package Python : l'app web est servie par FastAPI.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    outDir: "../src/flowmd/web/static",
    emptyOutDir: true,
  },
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});
