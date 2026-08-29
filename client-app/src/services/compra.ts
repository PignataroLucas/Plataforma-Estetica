import type { CompraPreparada } from '@/types/api';

import { authPost } from './http';

export interface ItemCompra {
  producto: number;
  cantidad: number;
}

/**
 * POST /api/client/comprar/ — emite el cupón y devuelve qué abrir en el WebView.
 *
 * Se llama al tocar "Comprar" y no antes: cada llamada emite un cupón, y los que
 * no se usan hay que limpiarlos después (COMPRA_EN_APP_SPEC.md §6.5).
 */
export function prepararCompra(items: ItemCompra[], centroId?: number): Promise<CompraPreparada> {
  const query = centroId ? `?centro=${centroId}` : '';
  return authPost<CompraPreparada>(`/client/comprar/${query}`, { items });
}
