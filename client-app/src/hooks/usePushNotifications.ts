/**
 * Conecta las notificaciones push con la sesión y con la navegación.
 *
 * Hace tres cosas:
 * - Registra el teléfono cuando hay sesión (y una sola vez por sesión).
 * - Lleva a la pantalla correcta cuando se toca una notificación.
 * - Refresca los datos que la notificación acaba de invalidar.
 *
 * Va montado una sola vez, en el layout raíz. **Nada de esto puede romper la
 * app**: donde no hay notificaciones el hook no hace nada y el resto sigue
 * andando igual. Por eso `expo-notifications` se pide en diferido y no se
 * importa arriba (ver `services/notificacionesNativas.ts`).
 */
import { useQueryClient } from '@tanstack/react-query';
import { router } from 'expo-router';
import { useCallback, useEffect, useRef } from 'react';

// Solo tipos: se borra en compilación, no ejecuta el módulo.
import type * as ExpoNotifications from 'expo-notifications';

import { notificaciones } from '@/services/notificacionesNativas';
import { crearCanalesAndroid, registrarDispositivo } from '@/services/push';
import { useAuthStore } from '@/stores/auth';

/** Carga útil que manda el backend en cada aviso (ver `despacho.py`). */
interface DatosDeAviso {
  evento?: string;
  ruta?: string;
  turnoId?: number;
  avisoId?: number;
}

function datosDe(notificacion: ExpoNotifications.Notification): DatosDeAviso {
  return (notificacion.request.content.data ?? {}) as DatosDeAviso;
}

export function usePushNotifications() {
  const status = useAuthStore((s) => s.status);
  const autenticado = status === 'authenticated';
  const queryClient = useQueryClient();

  // El registro es una llamada de red: no se repite en cada render del layout.
  const yaRegistrado = useRef(false);
  // Los taps pueden llegar por dos vías (listener y último response en frío);
  // se recuerda cuál se atendió para no navegar dos veces al mismo lugar.
  const tapsAtendidos = useRef(new Set<string>());

  /**
   * Un aviso significa que algo cambió del lado del centro. Se invalida lo que
   * corresponda para que la pantalla no muestre el estado viejo al abrirse.
   */
  const invalidar = useCallback(
    (datos: DatosDeAviso) => {
      const evento = datos.evento ?? '';
      if (evento.startsWith('turno')) {
        // 'mis-turnos' y no 'turnos': React Query matchea por prefijo, y con la
        // clave equivocada esta invalidación no alcanzaba a ninguna query. El
        // aviso llegaba y la lista seguía mostrando el estado viejo.
        queryClient.invalidateQueries({ queryKey: ['mis-turnos'] });
      } else if (evento.startsWith('rutina')) {
        queryClient.invalidateQueries({ queryKey: ['mi-rutina'] });
      }
    },
    [queryClient],
  );

  const atenderTap = useCallback(
    (respuesta: ExpoNotifications.NotificationResponse) => {
      const id = respuesta.notification.request.identifier;
      if (tapsAtendidos.current.has(id)) return;
      tapsAtendidos.current.add(id);

      const datos = datosDe(respuesta.notification);
      invalidar(datos);

      // Sin sesión no hay adónde llevarla: el gate de navegación la manda a
      // login igual, y al entrar cae en el inicio.
      if (datos.ruta && autenticado) {
        router.push(datos.ruta as never);
      }
    },
    [invalidar, autenticado],
  );

  // --- Canales de Android ---
  // Independiente de la sesión: las notificaciones locales del simulador viajan
  // por estos mismos canales.
  useEffect(() => {
    crearCanalesAndroid().catch((error) => {
      console.warn('[push] No se pudieron crear los canales de Android:', error);
    });
  }, []);

  // --- Registro del dispositivo ---
  useEffect(() => {
    if (!autenticado) {
      // Al cerrar sesión se habilita volver a registrar en el próximo login
      // (puede ser otra cuenta en el mismo teléfono).
      yaRegistrado.current = false;
      return;
    }
    if (yaRegistrado.current) return;
    yaRegistrado.current = true;
    registrarDispositivo();
  }, [autenticado]);

  // --- App abierta ---
  useEffect(() => {
    const N = notificaciones();
    if (!N) return;

    let recibida: ExpoNotifications.EventSubscription | undefined;
    let tocada: ExpoNotifications.EventSubscription | undefined;

    try {
      // Con la app en pantalla no se navega sola --sería arrebatarle la vista a
      // la clienta-- pero sí se refrescan los datos por detrás.
      recibida = N.addNotificationReceivedListener((notificacion) => {
        invalidar(datosDe(notificacion));
      });
      tocada = N.addNotificationResponseReceivedListener(atenderTap);
    } catch (error) {
      console.warn('[push] No se pudieron registrar los listeners:', error);
    }

    return () => {
      recibida?.remove();
      tocada?.remove();
    };
  }, [invalidar, atenderTap]);

  // --- App abierta DESDE la notificación (arranque en frío) ---
  // El listener de arriba no se entera de este caso: la app todavía no existía
  // cuando se tocó la notificación.
  //
  // Se consulta con la variante asíncrona y NO con `useLastNotificationResponse()`:
  // ese hook lanza donde el módulo nativo no está y, al ser un hook, la excepción
  // sube durante el render y se lleva puesto todo el navegador.
  useEffect(() => {
    const N = notificaciones();
    if (!N) return;

    let vigente = true;
    (async () => {
      try {
        const respuesta = await N.getLastNotificationResponseAsync();
        if (vigente && respuesta) atenderTap(respuesta);
      } catch {
        // Sin soporte nativo no hay arranque en frío que atender.
      }
    })();
    return () => {
      vigente = false;
    };
  }, [atenderTap]);
}
