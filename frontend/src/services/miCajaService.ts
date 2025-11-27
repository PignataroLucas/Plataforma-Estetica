import api from './api'
import type {
  CobrarTurnoRequest,
  CobrarTurnoResponse,
  VenderProductoRequest,
  VenderProductoResponse,
  TurnosPendientesResponse,
  ResumenDiario,
  MisTransaccionesResponse,
  CierreCajaRequest,
  CierreCajaResponse
} from '@/types/miCaja'

/**
 * Mi Caja Services - Employee Point of Sale System
 * API calls for transaction registration and cash register operations
 */

// ==================== TRANSACTION OPERATIONS ====================

/**
 * Register payment for a completed appointment
 */
export const cobrarTurno = async (data: CobrarTurnoRequest) => {
  const response = await api.post<CobrarTurnoResponse>('/mi-caja/cobrar-turno/', data)
  return response.data
}

/**
 * Sell a product and update inventory
 */
export const venderProducto = async (data: VenderProductoRequest) => {
  const response = await api.post<VenderProductoResponse>('/mi-caja/vender-producto/', data)
  return response.data
}

// ==================== TRANSACTION QUERIES ====================

/**
 * Get transactions created by current user
 * @param fecha - Date in YYYY-MM-DD format (optional, defaults to today)
 * @param payment_method - Filter by payment method (optional)
 */
export const getMisTransacciones = async (fecha?: string, payment_method?: string) => {
  const params: any = {}
  if (fecha) params.fecha = fecha
  if (payment_method) params.payment_method = payment_method

  const response = await api.get<MisTransaccionesResponse>('/mi-caja/mis-transacciones/', { params })
  return response.data
}

/**
 * Get daily summary for current employee
 * @param fecha - Date in YYYY-MM-DD format (optional, defaults to today)
 */
export const getResumenDia = async (fecha?: string) => {
  const params: any = {}
  if (fecha) params.fecha = fecha

  const response = await api.get<ResumenDiario>('/mi-caja/resumen-dia/', { params })
  return response.data
}

/**
 * Get completed appointments without payment registered
 */
export const getTurnosPendientesCobro = async () => {
  const response = await api.get<TurnosPendientesResponse>('/mi-caja/turnos-pendientes-cobro/')
  return response.data
}

// ==================== CASH REGISTER CLOSING ====================

/**
 * Create a cash register closing record
 */
export const cerrarCaja = async (data: CierreCajaRequest) => {
  const response = await api.post<CierreCajaResponse>('/mi-caja/cierre-caja/', data)
  return response.data
}
