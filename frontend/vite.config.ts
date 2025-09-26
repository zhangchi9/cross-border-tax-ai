import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    watch: {
      usePolling: true, // Enable polling for better Windows/Docker compatibility
    },
    hmr: {
      clientPort: 5173, // Ensure HMR works in Docker
    },
    proxy: {
      '/api': {
        target: 'http://tax-consultant-backend-dev:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})