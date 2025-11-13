/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  // Agregar más variables de entorno aquí
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
