/**
 * Lo que hace falta para pintar la rutina del día.
 *
 * Los días van como `date.weekday()` del backend: 0 = lunes … 6 = domingo. Las
 * fechas llegan como `YYYY-MM-DD` en el día del centro y se leen tal cual, sin
 * pasar por `Date` con zona: "hoy" lo decide el backend, no el reloj del teléfono.
 */
import type { MiRutina, MomentoRutina, RutinaHoy, RutinaItem } from '@/types/api';

export const DIAS_CORTOS = ['L', 'M', 'M', 'J', 'V', 'S', 'D'];
const DIAS_LARGOS = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo'];
const MESES = [
  'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
];

export const MOMENTOS: MomentoRutina[] = ['DIURNA', 'NOCTURNA'];

const capitalizar = (texto: string) => texto.charAt(0).toUpperCase() + texto.slice(1);

/** "Martes y viernes", "Solo los domingos". Vacío = todos los días. */
export function describirDias(dias: number[]): string {
  if (dias.length === 0) return 'Todos los días';
  const nombres = [...dias].sort((a, b) => a - b).map((d) => DIAS_LARGOS[d]);
  if (nombres.length === 1) {
    const dia = nombres[0];
    return `Solo los ${dia.endsWith('s') ? dia : `${dia}s`}`;
  }
  return capitalizar(`${nombres.slice(0, -1).join(', ')} y ${nombres[nombres.length - 1]}`);
}

/** Partes de una fecha `YYYY-MM-DD`, con el día de la semana a la manera del backend. */
export function partesDeFecha(iso: string) {
  const [anio, mes, dia] = iso.split('-').map(Number);
  // getUTCDay: 0 = domingo. Se corre para que 0 sea lunes.
  const diaSemana = (new Date(Date.UTC(anio, mes - 1, dia)).getUTCDay() + 6) % 7;
  return { anio, mes, dia, diaSemana };
}

/** "Viernes 16 de octubre". */
export function fechaLarga(iso: string): string {
  const { mes, dia, diaSemana } = partesDeFecha(iso);
  return `${capitalizar(DIAS_LARGOS[diaSemana])} ${dia} de ${MESES[mes - 1]}`;
}

/** Los momentos que hoy tienen al menos un paso. */
export function momentosDeHoy(hoy: RutinaHoy): MomentoRutina[] {
  return MOMENTOS.filter((m) => hoy.momentos[m].total > 0);
}

/** ¿Completó todo lo que tocaba hoy? */
export function rutinaDeHoyCompleta(hoy: RutinaHoy): boolean {
  const momentos = momentosDeHoy(hoy);
  return momentos.length > 0 && momentos.every((m) => hoy.momentos[m].cumplido);
}

/** Una frase sobre cómo va el día, para el título de la tarjeta del inicio. */
export function resumenDelDia(hoy: RutinaHoy): string {
  const momentos = momentosDeHoy(hoy);
  if (momentos.length === 0) return 'Hoy no tenés pasos';
  if (rutinaDeHoyCompleta(hoy)) return 'Rutina de hoy completa';

  const pendientes = momentos.filter((m) => !hoy.momentos[m].cumplido);
  if (pendientes.length === 2) {
    const empezo = hoy.momentos.DIURNA.hechos + hoy.momentos.NOCTURNA.hechos > 0;
    return empezo ? 'Seguí con tu rutina' : 'Empezá con la de la mañana';
  }
  return pendientes[0] === 'DIURNA' ? 'Te falta la de la mañana' : 'Te falta la de la noche';
}

/**
 * El día como queda después de tildar o destildar un paso, calculado en el
 * teléfono para que el tilde se vea al instante.
 *
 * Replica las reglas del backend (`apps/clientes/rutina_diaria.py`): un momento
 * se cumple con todos sus pasos de hoy, y el día cuenta para la racha con que se
 * cumpla uno de los dos. La respuesta del servidor pisa esto apenas llega.
 */
export function aplicarTilde(datos: MiRutina, item: RutinaItem, hecho: boolean): MiRutina {
  const { hoy, rutina } = datos;
  if (!hoy || !rutina) return datos;

  const hechos = new Set(hoy.pasos_hechos);
  if (hecho) hechos.add(item.id);
  else hechos.delete(item.id);

  const momentos = { ...hoy.momentos };
  for (const momento of MOMENTOS) {
    const pasos = rutina.items.filter((i) => i.momento === momento && i.va_hoy);
    const cuantos = pasos.filter((p) => hechos.has(p.id)).length;
    momentos[momento] = {
      total: pasos.length,
      hechos: cuantos,
      cumplido: pasos.length > 0 && cuantos === pasos.length,
    };
  }

  const contabaHoy = MOMENTOS.some((m) => hoy.momentos[m].cumplido);
  const cuentaHoy = MOMENTOS.some((m) => momentos[m].cumplido);
  const racha = hoy.racha + (cuentaHoy === contabaHoy ? 0 : cuentaHoy ? 1 : -1);

  return {
    ...datos,
    hoy: {
      ...hoy,
      pasos_hechos: [...hechos].sort((a, b) => a - b),
      momentos,
      semana: hoy.semana.map((d) => (d.fecha === hoy.fecha ? { ...d, cumplido: cuentaHoy } : d)),
      racha: Math.max(0, racha),
    },
  };
}
