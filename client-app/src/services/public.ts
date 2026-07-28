import type { CentroPublico, Paginated, ProductoPublico, ServicioPublico } from '@/types/api';

import { apiGet } from './api';
import { DEFAULT_CENTRO_ID } from './config';

export const getCentroInfo = (centroId: number = DEFAULT_CENTRO_ID) =>
  apiGet<CentroPublico>(`/public/centros/${centroId}/info/`);

export const getServicios = (centroId: number = DEFAULT_CENTRO_ID) =>
  apiGet<Paginated<ServicioPublico>>(`/public/centros/${centroId}/servicios/`);

/** Ficha de un tratamiento. 404 si está inactivo o es de otro centro. */
export const getServicio = (id: number, centroId: number = DEFAULT_CENTRO_ID) =>
  apiGet<ServicioPublico>(`/public/centros/${centroId}/servicios/${id}/`);

export const getProductos = (centroId: number = DEFAULT_CENTRO_ID) =>
  apiGet<Paginated<ProductoPublico>>(`/public/centros/${centroId}/productos/`);
