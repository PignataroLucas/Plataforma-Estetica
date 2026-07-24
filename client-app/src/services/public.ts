import type { CentroPublico, Paginated, ProductoPublico, ServicioPublico } from '@/types/api';

import { apiGet } from './api';
import { DEFAULT_CENTRO_ID } from './config';

export const getCentroInfo = (centroId: number = DEFAULT_CENTRO_ID) =>
  apiGet<CentroPublico>(`/public/centros/${centroId}/info/`);

export const getServicios = (centroId: number = DEFAULT_CENTRO_ID) =>
  apiGet<Paginated<ServicioPublico>>(`/public/centros/${centroId}/servicios/`);

export const getProductos = (centroId: number = DEFAULT_CENTRO_ID) =>
  apiGet<Paginated<ProductoPublico>>(`/public/centros/${centroId}/productos/`);
