/**
 * Configuración de red de la app.
 *
 * En dev usamos localhost:8000 → funciona en web directo y en el emulador vía
 * `adb reverse tcp:8000 tcp:8000` (el Host queda 'localhost', permitido por Django).
 * Para un dispositivo físico habría que usar la IP LAN del host + agregarla a
 * ALLOWED_HOSTS (o usar túnel). Se resuelve cuando lleguemos a esa etapa.
 */
export const API_BASE_URL = 'http://localhost:8000/api';

/** Centro por defecto en dev. En producción lo define el onboarding (QR del centro). */
export const DEFAULT_CENTRO_ID = 1;
