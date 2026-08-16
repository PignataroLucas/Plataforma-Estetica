/**
 * Carrito de compra (Zustand).
 *
 * Vive en el dispositivo y en memoria: no se guarda en el backend ni sobrevive
 * a cerrar la app (COMPRA_EN_APP_SPEC.md §5.4). Si la clienta cambia de
 * teléfono, pierde el carrito, y está bien — quien valida stock y cobra es
 * Tienda Nube, así que un carrito viejo no vale nada.
 */
import { create } from 'zustand';

import type { ProductoPublico } from '@/types/api';

/**
 * Tope por producto.
 *
 * La API pública no expone disponibilidad a propósito (el stock que tenemos es
 * el del depósito, no el del mostrador), así que la app no puede saber cuántas
 * unidades hay. El tope no es un dato de stock: solo evita que un dedo pesado
 * arme un pedido de 300 unidades que Tienda Nube va a rechazar al pagar.
 */
export const MAX_POR_PRODUCTO = 20;

export interface ItemCarrito {
  productoId: number;
  nombre: string;
  marca: string;
  /**
   * Precio unitario al momento de agregar, tal como lo devolvió la API (que ya
   * aplica la oferta del catálogo). Es una copia para poder dibujar la fila sin
   * pedir nada; la pantalla del carrito relee el precio y prefiere el fresco.
   */
  precio: string;
  foto: string | null;
  cantidad: number;
}

interface CarritoState {
  /**
   * Centro dueño de estos items. El catálogo y los precios son por centro, así
   * que un carrito armado en otro no se puede reusar.
   */
  centroId: number | null;
  items: ItemCarrito[];

  agregar: (producto: ProductoPublico, centroId: number, cantidad?: number) => void;
  cambiarCantidad: (productoId: number, cantidad: number) => void;
  quitar: (productoId: number) => void;
  vaciar: () => void;
}

function acotar(cantidad: number): number {
  return Math.max(1, Math.min(MAX_POR_PRODUCTO, Math.trunc(cantidad)));
}

export const useCarritoStore = create<CarritoState>((set) => ({
  centroId: null,
  items: [],

  agregar: (producto, centroId, cantidad = 1) =>
    set((state) => {
      // Cambió el centro: lo de antes es de otro catálogo y otros precios.
      const items = state.centroId === centroId ? state.items : [];
      const actual = items.find((i) => i.productoId === producto.id);

      if (actual) {
        return {
          centroId,
          items: items.map((i) =>
            i.productoId === producto.id ? { ...i, cantidad: acotar(i.cantidad + cantidad) } : i,
          ),
        };
      }

      return {
        centroId,
        items: [
          ...items,
          {
            productoId: producto.id,
            nombre: producto.nombre,
            marca: producto.marca,
            precio: producto.precio,
            foto: producto.foto_thumb ?? producto.foto,
            cantidad: acotar(cantidad),
          },
        ],
      };
    }),

  cambiarCantidad: (productoId, cantidad) =>
    set((state) => {
      // Bajar de 1 es sacarlo: evita la fila fantasma en cero.
      if (cantidad < 1) {
        return { items: state.items.filter((i) => i.productoId !== productoId) };
      }
      return {
        items: state.items.map((i) =>
          i.productoId === productoId ? { ...i, cantidad: acotar(cantidad) } : i,
        ),
      };
    }),

  quitar: (productoId) =>
    set((state) => ({ items: state.items.filter((i) => i.productoId !== productoId) })),

  vaciar: () => set({ items: [], centroId: null }),
}));

/** Unidades totales — lo que muestra el globito del ícono. */
export function useUnidadesEnCarrito(): number {
  return useCarritoStore((s) => s.items.reduce((total, i) => total + i.cantidad, 0));
}

/** Cuántas unidades de un producto hay en el carrito (0 si no está). */
export function useCantidadDeProducto(productoId: number): number {
  return useCarritoStore(
    (s) => s.items.find((i) => i.productoId === productoId)?.cantidad ?? 0,
  );
}

/**
 * Vacía el carrito sin usar el hook. La usa el logout: el carrito vive en
 * memoria, así que sin esto la clienta que inicia sesión después en el mismo
 * teléfono se encuentra con el pedido de la anterior.
 */
export function vaciarCarrito(): void {
  useCarritoStore.getState().vaciar();
}
