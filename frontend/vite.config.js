import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  
  server: {
    port: 3000,
    proxy: {
      // Proxy API requests to Django backend
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Proxy authentication endpoints
      '/accounts': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Proxy static files if needed
      '/static': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Proxy media files
      '/media': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Proxy forum routes to Django-machina (except /forum route which is handled by React)
      '/forum/forum': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@pages': path.resolve(__dirname, './src/pages'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@styles': path.resolve(__dirname, './src/styles'),
      '@types': path.resolve(__dirname, './src/types'),
    },
  },
  
  build: {
    outDir: '../static/react',
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, 'index.html'),
      },
    },
  },
})