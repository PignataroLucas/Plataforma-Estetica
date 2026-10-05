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

/**
 * Zona horaria en la que se muestra todo instante: la del centro.
 *
 * Un turno es a las 16:00 **en el centro**, esté donde esté el teléfono. Con la
 * zona del dispositivo, una clienta de viaje —o un emulador configurado en
 * Europa, que es como apareció— ve el turno de las 16:00 a las 21:00, aunque la
 * grilla de horarios, que arma el backend, le haya mostrado las 16:00.
 *
 * Es la misma `TIME_ZONE` del backend. El día que haya centros en otra zona,
 * esto tiene que venir con el centro.
 */
export const ZONA_CENTRO = 'America/Argentina/Buenos_Aires';

/**
 * Respaldo si el motor no resuelve la zona. Argentina no tiene horario de
 * verano desde 2009; si lo vuelve a tener, el camino con `Intl` lo toma solo.
 */
const DESFASE_CENTRO_MS = -3 * 60 * 60 * 1000;

const DIAS_EN = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

interface PartesDeFecha {
  anio: number;
  /** 0-11, como `Date#getMonth`. */
  mes: number;
  dia: number;
  /** 0 = domingo, como `Date#getDay`. */
  diaSemana: number;
  hora: number;
  minuto: number;
}

let formateador: Intl.DateTimeFormat | null | undefined;

function formateadorDelCentro(): Intl.DateTimeFormat | null {
  if (formateador !== undefined) return formateador;
  try {
    formateador = new Intl.DateTimeFormat('en-US', {
      timeZone: ZONA_CENTRO,
      year: 'numeric',
      month: 'numeric',
      day: 'numeric',
      weekday: 'short',
      hour: 'numeric',
      minute: 'numeric',
      hourCycle: 'h23',
    });
  } catch {
    formateador = null;
  }
  return formateador;
}

function partesEnElCentro(fecha: Date): PartesDeFecha {
  const f = formateadorDelCentro();
  if (f) {
    try {
      const p: Record<string, string> = {};
      for (const parte of f.formatToParts(fecha)) p[parte.type] = parte.value;
      const partes = {
        anio: Number(p.year),
        mes: Number(p.month) - 1,
        dia: Number(p.day),
        diaSemana: DIAS_EN.indexOf(p.weekday),
        // Algunos motores dicen "24" para la medianoche aun con h23.
        hora: Number(p.hour) % 24,
        minuto: Number(p.minute),
      };
      if (partes.diaSemana >= 0 && Object.values(partes).every(Number.isFinite)) return partes;
    } catch {
      // Cae al desfase fijo.
    }
  }
  const d = new Date(fecha.getTime() + DESFASE_CENTRO_MS);
  return {
    anio: d.getUTCFullYear(),
    mes: d.getUTCMonth(),
    dia: d.getUTCDate(),
    diaSemana: d.getUTCDay(),
    hora: d.getUTCHours(),
    minuto: d.getUTCMinutes(),
  };
}

/** Las partes de un instante ISO en la zona del centro, o null si no es fecha. */
function partesDe(iso: string): PartesDeFecha | null {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? null : partesEnElCentro(d);
}

/** Formatea una fecha ISO a "Vie 1 Ago · 14:30 hs", en la hora del centro. */
export function formatFechaTurno(iso: string): string {
  const p = partesDe(iso);
  if (!p) return '';
  return `${DIAS[p.diaSemana]} ${p.dia} ${MESES[p.mes]} · ${formatHora(iso)}`;
}

/** "14:30 hs", en la hora del centro. */
export function formatHora(iso: string): string {
  const p = partesDe(iso);
  if (!p) return '';
  const hh = p.hora.toString().padStart(2, '0');
  const mm = p.minuto.toString().padStart(2, '0');
  return `${hh}:${mm} hs`;
}

/** "Martes 28 de julio", en la fecha del centro. */
export function formatFechaLarga(iso: string): string {
  const p = partesDe(iso);
  if (!p) return '';
  return `${DIAS_LARGOS[p.diaSemana]} ${p.dia} de ${MESES_LARGOS[p.mes]}`;
}

/** "28 Jul 2026" — compacto, para el historial. En la fecha del centro. */
export function formatFechaCorta(iso: string): string {
  const p = partesDe(iso);
  if (!p) return '';
  return `${p.dia} ${MESES[p.mes]} ${p.anio}`;
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

/**
 * Convierte el texto libre de `beneficios` en una lista.
 *
 * El campo es un TextField sin estructura, así que el centro escribe una línea
 * por beneficio y puede o no ponerle viñeta. Acá se limpia lo que haya puesto.
 * Lo usan la ficha del tratamiento y la del producto.
 */
export function parsearBeneficios(texto: string): string[] {
  return texto
    .split('\n')
    .map((linea) => linea.replace(/^[\s•\-–*]+/, '').trim())
    .filter(Boolean);
}
