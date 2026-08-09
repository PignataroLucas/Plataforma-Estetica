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

/**
 * Catálogo de productos del centro.
 *
 * El `page_size` es deliberado: la API pagina de a 20 y el centro ya tiene 31
 * productos, así que sin esto la grilla mostraría 20 y faltarían 11 sin que
 * nadie se entere. Un catálogo de cosmética no necesita paginar; si algún día
 * pasa de unos cientos, va scroll infinito de verdad en vez de subir este
 * número (el backend corta en 1000).
 */
export const getProductos = (centroId: number = DEFAULT_CENTRO_ID) =>
  apiGet<Paginated<ProductoPublico>>(
    `/public/centros/${centroId}/productos/?page_size=200`,
  );

/** Ficha de un producto. 404 si está inactivo, no es de reventa o es de otro centro. */
export const getProducto = (id: number, centroId: number = DEFAULT_CENTRO_ID) =>
  apiGet<ProductoPublico>(`/public/centros/${centroId}/productos/${id}/`);
