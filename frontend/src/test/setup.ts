/**
 * Preparación común de los tests del CRM. Corre antes de cada archivo
 * (`setupFiles` en vite.config.ts).
 */
import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'

// Testing Library solo se limpia sola cuando `globals` está prendido, y acá no
// lo está. Sin esto, el segundo `render()` de un archivo encuentra el DOM del
// primero y las queries fallan por encontrar todo dos veces.
afterEach(() => {
  cleanup()
})

// jsdom 26 no implementa la Object URL API: `URL.createObjectURL` directamente
// no existe. La usa la vista previa de la foto en ProductoForm, así que sin
// estos dos el caso feliz revienta con "is not a function" — y es justo el que
// tiene que pasar.
URL.createObjectURL = vi.fn(() => 'blob:jsdom/foto-de-prueba')
URL.revokeObjectURL = vi.fn()
