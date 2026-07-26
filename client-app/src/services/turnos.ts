/**
 * Turnos del cliente (client_api).
 *
 * Todo el scope lo resuelve el backend a partir del token: nunca se manda un
 * id de cliente. `centroId` solo elige la vinculación en cuentas multi-centro.
 */
import type {
  Disponibilidad,
  MisTurnos,
  ReservaPayload,
  ServiciosReservables,
  TurnoApp,
} from '@/types/api';

import { authGet, authPost } from './http';

const centroQuery = (centroId?: number) => (centroId ? `?centro=${centroId}` : '');

/**
 * GET /api/client/turnos/servicios/ — tratamientos reservables desde la app.
 * Es un subconjunto del catálogo: el centro marca cuáles se pueden reservar solo.
 */
export function getServiciosReservables(centroId?: number): Promise<ServiciosReservables> {
  return authGet<ServiciosReservables>(`/client/turnos/servicios/${centroQuery(centroId)}`);
}

/** GET /api/client/turnos/ — próximos + historial. */
export function getMisTurnos(centroId?: number): Promise<MisTurnos> {
  return authGet<MisTurnos>(`/client/turnos/${centroQuery(centroId)}`);
}

/** GET /api/client/turnos/disponibilidad/ — horarios libres de un servicio en un día. */
export function getDisponibilidad(
  servicioId: number,
  fecha: string,
  centroId?: number,
): Promise<Disponibilidad> {
  const params = new URLSearchParams({ servicio: String(servicioId), fecha });
  if (centroId) params.set('centro', String(centroId));
  return authGet<Disponibilidad>(`/client/turnos/disponibilidad/?${params.toString()}`);
}

/** POST /api/client/turnos/ — reserva un turno (queda pendiente de confirmación). */
export function reservarTurno(payload: ReservaPayload, centroId?: number): Promise<TurnoApp> {
  return authPost<TurnoApp>(`/client/turnos/${centroQuery(centroId)}`, payload);
}

/** POST /api/client/turnos/<id>/cancelar/ */
export function cancelarTurno(turnoId: number): Promise<TurnoApp> {
  return authPost<TurnoApp>(`/client/turnos/${turnoId}/cancelar/`);
}
