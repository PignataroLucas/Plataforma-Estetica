/**
 * Acceso controlado a `expo-notifications`.
 *
 * **En Expo Go sobre Android, importar `expo-notifications` lanza una
 * excepción.** No es un warning: el paquete ejecuta
 * `DevicePushTokenAutoRegistration` al cargarse, eso llama a
 * `warnOfExpoGoPushUsage()`, y esa función hace `throw` cuando detecta Expo Go
 * en Android (en iOS solo avisa por consola).
 *
 * Un `import` estático arriba de cualquier archivo que la app siempre carga
 * hace fallar la evaluación de ese módulo, y con ella la de todo lo que venga
 * después en la cadena. Los síntomas quedan lejísimos de la causa: la app
 * arranca a medias, y --lo que pasó acá-- el store de sesión nunca termina de
 * evaluarse, así que nunca registra el token en la capa de red y **todos los
 * requests salen sin `Authorization`**. Se ve como un 401 y parece un problema
 * de autenticación.
 *
 * Por eso el módulo se carga con `require()` y solo donde se puede. El import de
 * tipos es aparte y se borra en compilación, así que no ejecuta nada.
 */
import { isRunningInExpoGo } from 'expo';
import { Platform } from 'react-native';

// Solo tipos: TypeScript lo borra al compilar, no genera require.
import type * as ExpoNotifications from 'expo-notifications';

export type ModuloNotificaciones = typeof ExpoNotifications;

/** Por qué no se puede usar acá, para poder mostrarlo en pantalla. */
export const MOTIVO_NO_DISPONIBLE: string | null = (() => {
  if (Platform.OS === 'web') return 'En web no hay notificaciones nativas.';
  if (isRunningInExpoGo() && Platform.OS === 'android') {
    return 'Expo Go en Android no soporta notificaciones desde el SDK 53. Hace falta un development build (npx expo run:android).';
  }
  return null;
})();

export const NOTIFICACIONES_DISPONIBLES = MOTIVO_NO_DISPONIBLE === null;

// `undefined` = todavía no se intentó; `null` = se intentó y no está.
let modulo: ModuloNotificaciones | null | undefined;
let presentacionConfigurada = false;

/**
 * Devuelve el módulo, o `null` si en este entorno no se puede usar.
 *
 * Quien llama SIEMPRE tiene que contemplar el `null`: las notificaciones son
 * accesorias y que no estén nunca puede impedir usar la app.
 */
export function notificaciones(): ModuloNotificaciones | null {
  if (modulo !== undefined) return modulo;

  if (!NOTIFICACIONES_DISPONIBLES) {
    console.log(`[push] Sin notificaciones en este entorno. ${MOTIVO_NO_DISPONIBLE}`);
    modulo = null;
    return null;
  }

  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    modulo = require('expo-notifications') as ModuloNotificaciones;
    configurarPresentacion(modulo);
  } catch (error) {
    console.warn('[push] No se pudo cargar expo-notifications:', error);
    modulo = null;
  }
  return modulo;
}

/**
 * Cómo se muestra una notificación con la app abierta.
 *
 * Va acá y no a nivel de módulo porque depende de la carga diferida; se aplica
 * una sola vez, apenas el módulo está disponible.
 */
function configurarPresentacion(N: ModuloNotificaciones): void {
  if (presentacionConfigurada) return;
  presentacionConfigurada = true;
  N.setNotificationHandler({
    handleNotification: async () => ({
      shouldPlaySound: true,
      shouldSetBadge: false,
      shouldShowBanner: true,
      shouldShowList: true,
    }),
  });
}
