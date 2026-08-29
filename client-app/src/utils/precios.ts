/**
 * El precio que ve la clienta.
 *
 * Un solo lugar donde se aplica el descuento de la app, a propósito: la grilla,
 * la ficha y el carrito tienen que mostrar el mismo número, y ese número es el
 * que el checkout va a cobrar cuando el backend emita el cupón
 * (COMPRA_EN_APP_SPEC.md §5.8 y §6.1). Si cada pantalla hiciera su cuenta, la
 * clienta vería cambiar el precio justo cuando va a pagar.
 */

/** DRF manda los precios como string; un valor raro no puede romper un total. */
export function aNumero(precio: string | number): number {
  const n = typeof precio === 'string' ? parseFloat(precio) : precio;
  return Number.isFinite(n) ? n : 0;
}

/**
 * Aplica el porcentaje de descuento a un monto.
 *
 * Sin redondear: redondea `formatPrecio` al mostrar, y los totales se calculan
 * sobre el monto entero. El cupón de Tienda Nube se aplica sobre el total del
 * carrito, así que descontar acá línea por línea y sumar después daría una
 * diferencia de centavos contra lo que cobra el checkout.
 */
export function conDescuento(precio: string | number, porcentaje: number): number {
  const monto = aNumero(precio);
  if (!porcentaje) return monto;
  return monto * (1 - porcentaje / 100);
}

/** '15%' y no '15.00%': el backend manda el porcentaje con decimales. */
export function formatPorcentaje(porcentaje: number): string {
  return `${Number.isInteger(porcentaje) ? porcentaje : porcentaje.toFixed(1)}%`;
}
