import type { MiRutina, RutinaHoy } from '@/types/api';

import { authDelete, authGet, authPost } from './http';

/** GET /api/client/mi-rutina/ — rutina activa + plan del cliente vinculado. */
export function getMiRutina(centroId?: number): Promise<MiRutina> {
  const query = centroId ? `?centro=${centroId}` : '';
  return authGet<MiRutina>(`/client/mi-rutina/${query}`);
}

/**
 * Tilda (`hecho = true`) o destilda un paso de la rutina de hoy.
 *
 * Devuelve el día completo, así quien llama actualiza progreso y racha con la
 * respuesta y no necesita volver a pedir la rutina.
 */
export function marcarPaso(itemId: number, hecho: boolean): Promise<{ hoy: RutinaHoy }> {
  const path = `/client/mi-rutina/pasos/${itemId}/hecho/`;
  return hecho ? authPost(path) : authDelete(path);
}
