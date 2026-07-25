import type { MiRutina } from '@/types/api';

import { authGet } from './http';

/** GET /api/client/mi-rutina/ — rutina activa + plan del cliente vinculado. */
export function getMiRutina(centroId?: number): Promise<MiRutina> {
  const query = centroId ? `?centro=${centroId}` : '';
  return authGet<MiRutina>(`/client/mi-rutina/${query}`);
}
