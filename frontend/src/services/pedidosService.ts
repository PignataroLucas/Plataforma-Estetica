import api from './api'
import type { TurnoList } from '../types/models'

/**
 * Los pedidos de turno que llegan desde la app y esperan una respuesta del centro.
 *
 * Ver APROBACION_TURNOS_SPEC.md. Lo que hay que tener presente desde acá:
 *
 * - **Lo pendiente se deriva del turno**, no de un contador aparte: el backend
 *   devuelve los turnos que siguen en `PENDIENTE` y vienen de la app. Así no hay
 *   un segundo estado que se pueda desincronizar.
 * - **Un 409 no es un error de red ni un bug.** Significa que alguien del centro
 *   resolvió ese pedido primero, y hay que decírselo con todas las letras en vez
 *   de mostrar "algo salió mal".
 */

export interface PedidoPendiente extends TurnoList {
  /** Hasta cuándo se puede responder. Null en los que no vencen. */
  vence_en: string | null
  cliente_telefono: string | null
}

export interface MotivoRechazo {
  valor: string
  etiqueta: string
}

/**
 * El router del backend se monta en `api/turnos/` y registra `turnos` adentro,
 * así que las rutas llevan el segmento dos veces, igual que en `useTurnos.ts`.
 * Con uno solo el backend responde 404 y la bandeja se ve vacía: pasó en
 * producción, con un pedido real esperando.
 */
const TURNOS = '/turnos/turnos'

/** Se lanza cuando el backend responde 409: el pedido ya estaba resuelto. */
export class PedidoYaResuelto extends Error {}

export const getPedidosPendientes = async (): Promise<PedidoPendiente[]> => {
  const { data } = await api.get<{ count: number; results: PedidoPendiente[] }>(
    `${TURNOS}/pendientes_de_aprobacion/`
  )
  return data.results
}

export const getMotivosDeRechazo = async (): Promise<MotivoRechazo[]> => {
  const { data } = await api.get<MotivoRechazo[]>(`${TURNOS}/motivos_de_rechazo/`)
  return data
}

const traducirConflicto = (error: unknown): never => {
  const status = (error as { response?: { status?: number } })?.response?.status
  if (status === 409) {
    const detalle = (error as { response?: { data?: { detail?: string } } })
      ?.response?.data?.detail
    throw new PedidoYaResuelto(detalle || 'Alguien resolvió este pedido antes')
  }
  throw error
}

export const aprobarPedido = async (id: number): Promise<void> => {
  try {
    await api.post(`${TURNOS}/${id}/aprobar/`)
  } catch (error) {
    traducirConflicto(error)
  }
}

export const rechazarPedido = async (
  id: number,
  motivo: string,
  detalle = ''
): Promise<void> => {
  try {
    await api.post(`${TURNOS}/${id}/rechazar/`, { motivo, detalle })
  } catch (error) {
    traducirConflicto(error)
  }
}
