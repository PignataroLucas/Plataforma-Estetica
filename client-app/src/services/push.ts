/**
 * Notificaciones push: permisos, token y registro contra el backend.
 *
 * `expo-notifications` NO se importa acá directamente: se pide a
 * `notificacionesNativas`, que lo carga en diferido y devuelve `null` donde no
 * se puede usar. Importarlo estático rompe la app entera en Expo Go sobre
 * Android (ver el comentario de ese archivo).
 *
 * Además del entorno, para que el push remoto funcione hacen falta dos cosas
 * que no dependen del código:
 *
 * 1. Un `projectId` de EAS, que exige `getExpoPushTokenAsync`. Sale de `eas init`.
 * 2. Un development build: Expo Go no recibe push remoto en Android.
 *
 * Si falta cualquiera de las dos, el registro se saltea, queda el motivo en
 * consola y el resto de la app sigue funcionando igual.
 */
import Constants from 'expo-constants';
import * as Device from 'expo-device';
import { Platform } from 'react-native';

import { authDelete, authGet, authPatch, authPost } from './http';
import { notificaciones } from './notificacionesNativas';

/** Categorías del backend. Cada una es un canal de Android. */
export const CATEGORIAS = ['TURNOS', 'RUTINA', 'NOVEDADES', 'PROMOCIONES'] as const;
export type Categoria = (typeof CATEGORIAS)[number];

export type Preferencias = Record<Categoria, boolean>;

const NOMBRES_DE_CANAL: Record<Categoria, string> = {
  TURNOS: 'Turnos',
  RUTINA: 'Mi rutina',
  NOVEDADES: 'Novedades',
  PROMOCIONES: 'Promociones',
};

/** El token del aparato, para poder darlo de baja al cerrar sesión. */
let tokenActual: string | null = null;

function projectId(): string | null {
  const extra = Constants.expoConfig?.extra as
    | { eas?: { projectId?: string } }
    | undefined;
  return extra?.eas?.projectId ?? Constants.easConfig?.projectId ?? null;
}

/**
 * Crea un canal de Android por categoría.
 *
 * Le da al sistema operativo la misma granularidad que tienen las preferencias
 * de la app: alguien puede silenciar Promociones desde los ajustes de Android
 * sin perderse los turnos.
 *
 * Se llama al arrancar y no solo al registrar el dispositivo: los canales tienen
 * que existir aunque no haya push remoto, porque las notificaciones locales
 * --las del simulador-- viajan por los mismos canales.
 */
export async function crearCanalesAndroid(): Promise<void> {
  if (Platform.OS !== 'android') return;

  const N = notificaciones();
  if (!N) return;

  await Promise.all(
    CATEGORIAS.map((categoria) =>
      N.setNotificationChannelAsync(categoria.toLowerCase(), {
        name: NOMBRES_DE_CANAL[categoria],
        importance:
          categoria === 'TURNOS'
            ? N.AndroidImportance.HIGH
            : N.AndroidImportance.DEFAULT,
      }),
    ),
  );
}

/** Pide permiso si todavía no lo dio. No vuelve a preguntar si ya lo negó. */
async function tenemosPermiso(): Promise<boolean> {
  const N = notificaciones();
  if (!N) return false;

  const { status } = await N.getPermissionsAsync();
  if (status === 'granted') return true;
  // 'denied' en iOS es definitivo: volver a pedirlo no muestra nada.
  if (status === 'denied') return false;

  const pedido = await N.requestPermissionsAsync({
    ios: { allowAlert: true, allowBadge: true, allowSound: true },
  });
  return pedido.status === 'granted';
}

/**
 * Registra este teléfono para recibir push.
 *
 * Se llama después del login. Devuelve el token si quedó registrado, o null con
 * el motivo en consola.
 */
export async function registrarDispositivo(): Promise<string | null> {
  const N = notificaciones();
  if (!N) return null;

  if (!Device.isDevice) {
    // No se corta acá: un emulador de Android con Google Play services sí recibe
    // push, y es la forma más barata de probar el circuito completo. Si el
    // entorno no lo soporta, `getExpoPushTokenAsync` falla y lo agarra el catch.
    console.log(
      '[push] Emulador detectado. Va a funcionar si la imagen tiene Google Play services.',
    );
  }

  const proyecto = projectId();
  if (!proyecto) {
    console.warn(
      '[push] Falta el projectId de EAS (correr `eas init`). No se registra el dispositivo.',
    );
    return null;
  }

  try {
    if (!(await tenemosPermiso())) {
      console.log('[push] La clienta no dio permiso de notificaciones.');
      return null;
    }

    const { data: token } = await N.getExpoPushTokenAsync({ projectId: proyecto });

    await authPost('/client/push/register/', {
      push_token: token,
      plataforma: Platform.OS === 'ios' ? 'IOS' : Platform.OS === 'android' ? 'ANDROID' : 'WEB',
    });

    tokenActual = token;
    return token;
  } catch (error) {
    console.warn('[push] No se pudo registrar el dispositivo:', error);
    return null;
  }
}

/**
 * Da de baja este teléfono. Se llama al cerrar sesión, **antes** de soltar el
 * token de sesión, porque el endpoint pide autenticación.
 *
 * Nunca lanza: que falle la baja no puede impedir cerrar sesión.
 */
export async function darDeBajaDispositivo(): Promise<void> {
  if (!tokenActual) return;
  try {
    await authDelete('/client/push/register/', { push_token: tokenActual });
  } catch (error) {
    console.warn('[push] No se pudo dar de baja el dispositivo:', error);
  } finally {
    tokenActual = null;
  }
}

/** GET /api/client/notificaciones/preferencias/ */
export function getPreferencias(): Promise<Preferencias> {
  return authGet<Preferencias>('/client/notificaciones/preferencias/');
}

/** PATCH /api/client/notificaciones/preferencias/ — manda solo lo que cambió. */
export function actualizarPreferencias(cambios: Partial<Preferencias>): Promise<Preferencias> {
  return authPatch<Preferencias>('/client/notificaciones/preferencias/', cambios);
}
