import path from 'path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0', // Allow access from outside container
    port: 5173,      // Explicitly set port
    strictPort: true, // Fail if port is already in use
    watch: {
      usePolling: true, // Required for Docker on some systems
    },
  },
});
