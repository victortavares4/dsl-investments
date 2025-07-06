import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    host: '127.0.0.1', // Força IPv4
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000', // Usa IPv4 explicitamente
        changeOrigin: true,
        secure: false,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('🔴 Proxy error:', err.message);
            console.log('💡 Certifique-se de que o servidor Flask está rodando em http://127.0.0.1:5000');
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('📡 Enviando requisição:', req.method, req.url);
          });
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            console.log('✅ Resposta recebida:', proxyRes.statusCode, req.url);
          });
        },
      },
    },
  },
  preview: {
    port: 3000,
    host: '127.0.0.1',
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['lucide-react'],
        },
      },
    },
  },
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
  },
})