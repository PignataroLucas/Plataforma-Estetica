/**
 * Configuración de red de la app.
 *
 * En dev usamos localhost:8000 → funciona en web directo y en el emulador vía
 * `adb reverse tcp:8000 tcp:8000` (el Host queda 'localhost', permitido por Django).
 * Para un dispositivo físico habría que usar la IP LAN del host + agregarla a
 * ALLOWED_HOSTS (o usar túnel). Se resuelve cuando lleguemos a esa etapa.
 */
export const API_BASE_URL = 'http://localhost:8000/api';

/** Origen para archivos de media (fotos): mismo host que la API, sin el /api. */
export const MEDIA_BASE_URL = API_BASE_URL.replace(/\/api\/?$/, '');

/** Resuelve la URL de una foto del backend (que llega relativa, ej: /media/...). */
export function resolveMediaUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  return /^https?:\/\//.test(path) ? path : `${MEDIA_BASE_URL}${path}`;
}

/** Centro por defecto en dev. En producción lo define el onboarding (QR del centro). */
export const DEFAULT_CENTRO_ID = 1;
