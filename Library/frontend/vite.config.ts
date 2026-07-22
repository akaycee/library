import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Single-process deployment: build output goes into the backend's static dir so
// FastAPI serves the SPA and the API from one origin. In dev, proxy /api to the
// backend for hot-reload.
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../backend/src/static',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
});
