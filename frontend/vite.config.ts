/// <reference types="vitest/config" />
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
    host: true,
    port: 5173,
    watch: {
      usePolling: true
    }
  },
  test: {
    // jsdom solo para lo que toca el DOM sería más rápido, pero mezclar entornos
    // por archivo se olvida y falla raro. Uno solo para todo.
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    // `globals` queda apagado (el default): cada test importa describe/it/expect
    // de 'vitest'. Prenderlo obligaría a declarar `types` en tsconfig, y esa
    // entrada apaga la inclusión automática del resto de los @types.
  },
})
