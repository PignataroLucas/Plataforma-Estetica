/** Formatea un precio (string o number) al formato argentino: $26.000 */
export function formatPrecio(precio: string | number): string {
  const n = Math.round(typeof precio === 'string' ? parseFloat(precio) : precio);
  if (Number.isNaN(n)) return '$0';
  const conSeparador = n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return `$${conSeparador}`;
}
