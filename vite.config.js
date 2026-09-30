import path from 'path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  server: {
    watch: {
      ignored: [
        path.resolve(__dirname, "src/BuildSync DB.png"),
        path.resolve(__dirname, "src/BuildSync Square Logo.png"),
      ],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  plugins: [react()],
})
