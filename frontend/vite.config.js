import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/auth': 'http://localhost:8000',
      '/reports': 'http://localhost:8000',
      '/search': 'http://localhost:8000',
      '/claims': 'http://localhost:8000',
      '/admin': 'http://localhost:8000',
      '/places': 'http://localhost:8000',
      '/notifications': 'http://localhost:8000',
      '/files': 'http://localhost:8000',
      '/health': 'http://localhost:8000'
    }
  }
});
