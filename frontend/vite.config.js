import { defineConfig } from 'vite';

// El frontend se sirve en http://localhost:5173 y reenvía /api al backend
// FastAPI (http://localhost:8000) sin sufrir problemas de CORS.
export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: true,
      },
      '/uploads': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
