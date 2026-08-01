import { useState } from 'react'
import {
  addMonths,
  eachDayOfInterval,
  endOfMonth,
  format,
  isBefore,
  isSameMonth,
  startOfMonth,
  startOfToday,
  subMonths,
} from 'date-fns'
import { es } from 'date-fns/locale'

/**
 * Calendario mensual de selección múltiple para las fechas puntuales de un servicio.
 *
 * Se usa cuando la disponibilidad no sigue un patrón semanal: la máquina alquilada
 * viene el viernes 20 y el sábado 28, y no hay "todos los viernes" que valga.
 * Las fechas viajan al backend como strings 'YYYY-MM-DD'.
 */

interface CalendarioFechasProps {
  /** Fechas elegidas en formato YYYY-MM-DD. */
  fechas: string[]
  onChange: (fechas: string[]) => void
}

/** La semana arranca en lunes (formato local, no el domingo del `getDay()` de JS). */
const CABECERA_DIAS = ['L', 'M', 'M', 'J', 'V', 'S', 'D']

const ISO = 'yyyy-MM-dd'

export default function CalendarioFechas({ fechas, onChange }: CalendarioFechasProps) {
  const hoy = startOfToday()
  const [mes, setMes] = useState<Date>(() => startOfMonth(mesInicial(fechas, hoy)))

  const seleccionadas = new Set(fechas)

  const toggle = (iso: string) => {
    onChange(
      seleccionadas.has(iso)
        ? fechas.filter(f => f !== iso)
        : [...fechas, iso].sort()
    )
  }

  // Se puede retroceder hasta el mes actual: cargar fechas pasadas no sirve de nada.
  const puedeRetroceder = !isSameMonth(mes, hoy)

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-3">
      <div className="flex items-center justify-between mb-2">
        <button
          type="button"
          onClick={() => setMes(subMonths(mes, 1))}
          disabled={!puedeRetroceder}
          aria-label="Mes anterior"
          className="h-7 w-7 flex items-center justify-center rounded-md text-gray-600 hover:bg-gray-100 disabled:opacity-30 disabled:hover:bg-transparent"
        >
          ‹
        </button>
        <span className="text-sm font-medium text-gray-900 capitalize">
          {format(mes, 'MMMM yyyy', { locale: es })}
        </span>
        <button
          type="button"
          onClick={() => setMes(addMonths(mes, 1))}
          aria-label="Mes siguiente"
          className="h-7 w-7 flex items-center justify-center rounded-md text-gray-600 hover:bg-gray-100"
        >
          ›
        </button>
      </div>

      <div className="grid grid-cols-7 gap-1 mb-1">
        {CABECERA_DIAS.map((dia, i) => (
          <span key={i} className="text-center text-[11px] font-medium text-gray-400">
            {dia}
          </span>
        ))}
      </div>

      <div className="grid grid-cols-7 gap-1">
        {celdasDelMes(mes).map((dia, i) => {
          if (!dia) return <span key={`hueco-${i}`} />

          const iso = format(dia, ISO)
          const activa = seleccionadas.has(iso)
          const pasada = isBefore(dia, hoy)

          return (
            <button
              key={iso}
              type="button"
              disabled={pasada}
              onClick={() => toggle(iso)}
              aria-pressed={activa}
              className={`h-8 rounded-md text-sm transition-colors ${
                pasada
                  ? 'text-gray-300 cursor-not-allowed'
                  : activa
                    ? 'bg-blue-600 text-white font-medium'
                    : 'text-gray-700 hover:bg-blue-50'
              }`}
            >
              {dia.getDate()}
            </button>
          )
        })}
      </div>

      {fechas.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <p className="text-xs text-gray-500 mb-1.5">
            {fechas.length} {fechas.length === 1 ? 'fecha elegida' : 'fechas elegidas'}
          </p>
          <div className="flex flex-wrap gap-1.5">
            {[...fechas].sort().map(iso => (
              <span
                key={iso}
                className="inline-flex items-center gap-1 rounded-full bg-blue-50 py-0.5 pl-2.5 pr-1 text-xs text-blue-800"
              >
                {format(parsearISO(iso), "EEE d 'de' MMM", { locale: es })}
                <button
                  type="button"
                  onClick={() => toggle(iso)}
                  aria-label={`Quitar ${iso}`}
                  className="h-4 w-4 flex items-center justify-center rounded-full text-blue-500 hover:bg-blue-200 hover:text-blue-900"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

/**
 * Mes en el que abre el calendario: el de la primera fecha que todavía no pasó.
 * Si están todas vencidas (o no hay ninguna), el mes actual — abrir en un mes
 * donde ya no se puede marcar nada solo confunde.
 */
function mesInicial(fechas: string[], hoy: Date): Date {
  const futura = [...fechas]
    .sort()
    .map(parsearISO)
    .find(fecha => !isBefore(fecha, hoy))
  return futura ?? hoy
}

/**
 * Días del mes alineados a una grilla de 7 columnas que arranca en lunes.
 * Los `null` son los huecos antes del día 1.
 */
function celdasDelMes(mes: Date): (Date | null)[] {
  const dias = eachDayOfInterval({ start: startOfMonth(mes), end: endOfMonth(mes) })
  // getDay(): 0 = domingo. Con la semana arrancando en lunes, el domingo va al final.
  const offset = (startOfMonth(mes).getDay() + 6) % 7
  return [...Array<null>(offset).fill(null), ...dias]
}

/**
 * 'YYYY-MM-DD' como fecha LOCAL. `new Date('2026-03-20')` la parsea como medianoche
 * UTC, que en Argentina (-03) cae el día anterior y mostraría un día de menos.
 */
function parsearISO(iso: string): Date {
  const [anio, mes, dia] = iso.split('-').map(Number)
  return new Date(anio, mes - 1, dia)
}
