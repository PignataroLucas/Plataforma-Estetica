/**
 * Que el CRM no calcule "hoy" en UTC.
 *
 * `new Date().toISOString()` convierte a UTC antes de escribir la fecha, así
 * que en Argentina (-03) a partir de las 21:00 el `.split('T')[0]` devuelve el
 * día siguiente. Con eso, Mi Caja abría en la fecha de mañana, el `max` del
 * selector dejaba elegir un día que todavía no pasó y la pestaña "hoy" de
 * turnos mostraba los de mañana.
 *
 * La zona se fija en `vite.config.ts` (`test.env.TZ`): sin eso, corriendo en
 * UTC no existe la franja donde el bug se ve y estos tests pasarían con el
 * código roto.
 *
 * Que nadie vuelva a escribir el patrón lo cuida ESLint (`no-restricted-syntax`
 * en `.eslintrc.cjs`), no un test: es una regla de forma, y ahí se ve al
 * escribir en vez de al correr la suite. La mitad del backend está en
 * `backend/apps/finanzas/tests/test_zona_horaria.py`.
 */
import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  formatDateArgentina,
  formatDateForInput,
  getTodayForInput,
} from '../dateUtils'

/** Viernes 4 de septiembre de 2026, 21:16 en Buenos Aires. En UTC ya es sábado 5. */
const NOCHE = new Date('2026-09-05T00:16:00Z')

/** El mismo viernes a las 15:00, cuando la fecha local y la UTC todavía coinciden. */
const TARDE = new Date('2026-09-04T18:00:00Z')

afterEach(() => {
  vi.useRealTimers()
})

function conElRelojEn(momento: Date) {
  vi.useFakeTimers()
  vi.setSystemTime(momento)
}

describe('la franja peligrosa', () => {
  it('a las 21:16 la fecha UTC y la local son días distintos', () => {
    conElRelojEn(NOCHE)

    // Sin esto, los tests de abajo podrían estar pasando por el motivo
    // equivocado: si el reloj no cayera en esta franja, no habría nada que ver.
    // Es el único lugar donde el patrón prohibido se escribe a propósito: es
    // justamente lo que se está midiendo.
    // eslint-disable-next-line no-restricted-syntax
    expect(new Date().toISOString().split('T')[0]).toBe('2026-09-05')
    expect(getTodayForInput()).toBe('2026-09-04')
  })

  it('a las 15:00 coinciden, y por eso el bug pasaba desapercibido de día', () => {
    conElRelojEn(TARDE)

    // eslint-disable-next-line no-restricted-syntax
    expect(new Date().toISOString().split('T')[0]).toBe('2026-09-04')
    expect(getTodayForInput()).toBe('2026-09-04')
  })
})

describe('getTodayForInput', () => {
  it('un viernes a la noche devuelve el viernes', () => {
    conElRelojEn(NOCHE)

    expect(getTodayForInput()).toBe('2026-09-04')
  })
})

describe('formatDateForInput', () => {
  it('toma la fecha del día local, no la del instante en UTC', () => {
    expect(formatDateForInput(NOCHE)).toBe('2026-09-04')
  })

  it('no corre un día una fecha que ya viene sin hora', () => {
    expect(formatDateForInput('2026-09-04')).toBe('2026-09-04')
  })
})

describe('formatDateArgentina', () => {
  it('no corre un día una fecha del backend', () => {
    // El backend manda 'YYYY-MM-DD' pelado. `new Date('2026-09-04')` lo
    // interpreta como medianoche UTC, que acá es el 3 a las 21:00.
    expect(formatDateArgentina('2026-09-04')).toBe('04/09/2026')
  })
})
