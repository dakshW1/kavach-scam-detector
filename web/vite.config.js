import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Everything (fonts, three.js, Vanta, Lenis) is bundled into dist/, so the site works with no internet.
export default defineConfig({
  plugins: [react()],
  server: { proxy: { '/api': 'http://127.0.0.1:8000' } },
  build: { outDir: 'dist', chunkSizeWarningLimit: 1500 },
});
