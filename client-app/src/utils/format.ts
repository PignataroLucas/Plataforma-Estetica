/** Formatea un precio (string o number) al formato argentino: $26.000 */
export function formatPrecio(precio: string | number): string {
  const n = Math.round(typeof precio === 'string' ? parseFloat(precio) : precio);
  if (Number.isNaN(n)) return '$0';
  const conSeparador = n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return `$${conSeparador}`;
}

const DIAS = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
const MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
const DIAS_LARGOS = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];
const MESES_LARGOS = [
  'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
];

/** Formatea una fecha ISO a "Vie 1 Ago · 14:30 hs" (hora local del dispositivo). */
export function formatFechaTurno(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  return `${DIAS[d.getDay()]} ${d.getDate()} ${MESES[d.getMonth()]} · ${formatHora(iso)}`;
}

/** "14:30 hs" */
export function formatHora(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  const hh = d.getHours().toString().padStart(2, '0');
  const mm = d.getMinutes().toString().padStart(2, '0');
  return `${hh}:${mm} hs`;
}

/** "Martes 28 de julio" */
export function formatFechaLarga(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  return `${DIAS_LARGOS[d.getDay()]} ${d.getDate()} de ${MESES_LARGOS[d.getMonth()]}`;
}

/** "28 Jul 2026" — compacto, para el historial. */
export function formatFechaCorta(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  return `${d.getDate()} ${MESES[d.getMonth()]} ${d.getFullYear()}`;
}

/**
 * Fecha en formato YYYY-MM-DD según la zona del dispositivo.
 * No usar `toISOString()`: convierte a UTC y en Argentina (-03) adelanta el día
 * a partir de las 21:00.
 */
export function fechaISOLocal(fecha: Date): string {
  const mes = (fecha.getMonth() + 1).toString().padStart(2, '0');
  const dia = fecha.getDate().toString().padStart(2, '0');
  return `${fecha.getFullYear()}-${mes}-${dia}`;
}

/**
 * Parsea 'YYYY-MM-DD' como fecha LOCAL.
 * `new Date('2026-07-27')` la interpreta como medianoche UTC, que en Argentina
 * (-03) cae el día anterior a las 21:00 — y el calendario mostraría un día de menos.
 */
export function parseFechaISOLocal(iso: string): Date {
  const [anio, mes, dia] = iso.split('-').map(Number);
  return new Date(anio, mes - 1, dia);
}

/**
 * Nombre del día como lo maneja el backend ('lunes', 'martes', ...).
 * OJO con el índice: `getDay()` arranca en domingo, mientras que el `weekday()`
 * de Python arranca en lunes. Este array está indexado por `getDay()`.
 */
const DIAS_BACKEND = [
  'domingo', 'lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado',
];

export function nombreDiaBackend(fecha: Date): string {
  return DIAS_BACKEND[fecha.getDay()];
}

/** Días habilitados en formato corto y en orden de semana: "Lun · Mar · Mié · Jue". */
export function formatDiasReserva(dias: string[]): string {
  return DIAS_BACKEND.map((nombre, i) => (dias.includes(nombre) ? DIAS[i] : null))
    .filter(Boolean)
    .join(' · ');
}

/** "Vie 20 Mar" — chip compacto para las fechas puntuales de un tratamiento. */
export function formatFechaChip(iso: string): string {
  const d = parseFechaISOLocal(iso);
  if (Number.isNaN(d.getTime())) return '';
  return `${DIAS[d.getDay()]} ${d.getDate()} ${MESES[d.getMonth()]}`;
}

/** "Marzo 2026" — encabezado del calendario mensual. */
export function formatMesAnio(fecha: Date): string {
  const mes = MESES_LARGOS[fecha.getMonth()];
  return `${mes.charAt(0).toUpperCase()}${mes.slice(1)} ${fecha.getFullYear()}`;
}

/** Etiquetas de un día para el selector de fechas: { diaSemana: 'Mar', numero: '28', mes: 'Jul' } */
export function etiquetasDeDia(fecha: Date) {
  return {
    diaSemana: DIAS[fecha.getDay()],
    numero: fecha.getDate().toString(),
    mes: MESES[fecha.getMonth()],
  };
}
