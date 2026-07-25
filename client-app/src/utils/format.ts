/** Formatea un precio (string o number) al formato argentino: $26.000 */
export function formatPrecio(precio: string | number): string {
  const n = Math.round(typeof precio === 'string' ? parseFloat(precio) : precio);
  if (Number.isNaN(n)) return '$0';
  const conSeparador = n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return `$${conSeparador}`;
}

const DIAS = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
const MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

/** Formatea una fecha ISO a "Vie 1 Ago · 14:30 hs" (hora local del dispositivo). */
export function formatFechaTurno(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  const hh = d.getHours().toString().padStart(2, '0');
  const mm = d.getMinutes().toString().padStart(2, '0');
  return `${DIAS[d.getDay()]} ${d.getDate()} ${MESES[d.getMonth()]} · ${hh}:${mm} hs`;
}
