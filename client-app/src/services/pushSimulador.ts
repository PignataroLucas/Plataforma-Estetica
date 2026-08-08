/**
 * Simulador de notificaciones para desarrollo.
 *
 * Programa notificaciones **locales** con exactamente la misma forma de carga útil
 * que manda el backend. Sirve para probar todo el lado del teléfono --el banner,
 * el canal de Android, el tap, el deep link y la invalidación de cache-- sin
 * cuenta de Expo y sin un teléfono real.
 *
 * **Necesita un development build en Android.** La doc de Expo dice que las
 * notificaciones locales siguen disponibles en Expo Go, y es cierto en iOS; en
 * Android el paquete ni siquiera se puede importar dentro de Expo Go, así que
 * tampoco hay simulación local. Con `npx expo run:android` funciona todo.
 *
 * Lo único que NO prueba es el transporte (que Expo entregue el mensaje). Eso se
 * verifica del lado del backend con `manage.py simular_notificacion`.
 *
 * Los textos son un espejo de `backend/apps/notificaciones/eventos.py`. Si allá
 * cambia la redacción, acá no hace falta seguirla: lo que se prueba es el camino,
 * no el contenido.
 */
import { notificaciones } from './notificacionesNativas';

interface AvisoDeMuestra {
  clave: string;
  etiqueta: string;
  titulo: string;
  cuerpo: string;
  categoria: 'turnos' | 'rutina' | 'novedades' | 'promociones';
  ruta: string;
}

export const AVISOS_DE_MUESTRA: AvisoDeMuestra[] = [
  {
    clave: 'turno_confirmado',
    etiqueta: 'Turno confirmado',
    titulo: 'Turno confirmado',
    cuerpo: 'Limpieza facial el 12 de agosto a las 15:00. Te esperamos.',
    categoria: 'turnos',
    ruta: '/turnos',
  },
  {
    clave: 'turno_recordatorio_24h',
    etiqueta: 'Recordatorio 24 h',
    titulo: 'Mañana tenés turno',
    cuerpo: 'Limpieza facial a las 15:00. Si no llegás, avisanos con tiempo.',
    categoria: 'turnos',
    ruta: '/turnos',
  },
  {
    clave: 'rutina_actualizada',
    etiqueta: 'Rutina actualizada',
    titulo: 'Actualizamos tu rutina',
    cuerpo: 'Tenés cambios en tu rutina de cuidado. Entrá a verlos.',
    categoria: 'rutina',
    ruta: '/mi-rutina',
  },
  {
    clave: 'cumpleanos',
    etiqueta: 'Cumpleaños',
    titulo: '¡Feliz cumple, Sofía!',
    cuerpo: 'Que lo pases hermoso. Te esperamos en AME.',
    categoria: 'novedades',
    ruta: '/promos',
  },
  {
    clave: 'oferta_nueva',
    etiqueta: 'Promoción',
    titulo: 'Nueva promo en AME',
    cuerpo: '2x1 en faciales. Hasta el 30 de agosto.',
    categoria: 'promociones',
    ruta: '/promos',
  },
];

/**
 * Segundos hasta que aparece. Un par de segundos alcanza para mandar la app al
 * fondo y ver la notificación como la ve la clienta, en vez del banner de
 * primer plano.
 */
export const DEMORA_SEGUNDOS = 3;

/**
 * Programa una notificación local con la carga útil de un aviso real.
 *
 * Devuelve el identificador que asigna el sistema, o `null` si en este entorno
 * no hay notificaciones nativas.
 */
export async function simularAviso(aviso: AvisoDeMuestra): Promise<string | null> {
  const N = notificaciones();
  if (!N) return null;

  return N.scheduleNotificationAsync({
    content: {
      title: aviso.titulo,
      body: aviso.cuerpo,
      sound: 'default',
      // Misma forma que arma `cola.py`: es lo que lee `usePushNotifications`.
      data: {
        evento: aviso.clave,
        ruta: aviso.ruta,
        avisoId: -1, // negativo: deja claro en los logs que es simulado
      },
    },
    trigger: {
      type: N.SchedulableTriggerInputTypes.TIME_INTERVAL,
      seconds: DEMORA_SEGUNDOS,
      // En Android el canal va en el trigger, no en el contenido.
      channelId: aviso.categoria,
    },
  });
}
