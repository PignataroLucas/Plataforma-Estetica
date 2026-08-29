import type { DescuentoApp } from '@/types/api';

import { authGet } from './http';

/** GET /api/client/descuento/ — el descuento de la app para la clienta logueada. */
export function getDescuentoApp(centroId?: number): Promise<DescuentoApp> {
  const query = centroId ? `?centro=${centroId}` : '';
  return authGet<DescuentoApp>(`/client/descuento/${query}`);
}
