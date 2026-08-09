/**
 * Configuración de red de la app.
 *
 * Por defecto apunta al backend local: funciona en web directo y en el emulador
 * vía `adb reverse tcp:8000 tcp:8000` (el Host queda 'localhost', permitido por
 * Django). Para un dispositivo físico habría que usar la IP LAN del host +
 * agregarla a ALLOWED_HOSTS (o usar túnel).
 *
 * `EXPO_PUBLIC_API_URL` en un `.env` lo sobreescribe, sin tocar código. Sirve
 * sobre todo para desarrollar contra producción: la base local no tiene el
 * contenido que carga el centro, así que el catálogo se ve vacío aunque todo
 * funcione. Ejemplo:
 *
 *     EXPO_PUBLIC_API_URL=https://plataforma-estetica-production.up.railway.app/api
 *
 * Ojo: Expo **inlinea** el valor al compilar, así que después de cambiarlo hay
 * que recargar la app entera, no alcanza con el fast refresh.
 *
 * Apuntar a producción es seguro para mirar: el catálogo son GET públicos y el
 * resto de la app queda detrás del gate de sesión, con tokens firmados por el
 * backend que los emitió. Aun así, lo que se ve es la base real del centro, y
 * cualquier dato raro puede ser un dato de verdad y no un bug.
 */
export const API_BASE_URL =
  // Tiene que ser una referencia estática con notación de punto: Expo la
  // reemplaza textualmente, y `process.env['...']` o desestructurar no funcionan.
  process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000/api';

/** Origen para archivos de media (fotos): mismo host que la API, sin el /api. */
export const MEDIA_BASE_URL = API_BASE_URL.replace(/\/api\/?$/, '');

/** Resuelve la URL de una foto del backend (que llega relativa, ej: /media/...). */
export function resolveMediaUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  return /^https?:\/\//.test(path) ? path : `${MEDIA_BASE_URL}${path}`;
}

/** Centro por defecto en dev. En producción lo define el onboarding (QR del centro). */
export const DEFAULT_CENTRO_ID = 1;
