import api from './api'
import type {
  VentaUnificadaRequest,
  VentaUnificadaResponse,
  EditarTransaccionRequest,
  EditarTransaccionResponse,
  EliminarTransaccionRequest,
  EliminarTransaccionResponse,
  TurnosPendientesResponse,
  ResumenDiario,
  MisTransaccionesResponse,
  CierreCajaRequest,
  CierreCajaResponse
} from '@/types/miCaja'

/**
 * Mi Caja Services - Employee Point of Sale System
 */

// ==================== TRANSACTION OPERATIONS ====================

/**
 * Register unified sale with multiple items (products, services, direct services)
 */
export const registrarVentaUnificada = async (data: VentaUnificadaRequest) => {
  const response = await api.post<VentaUnificadaResponse>('/mi-caja/venta-unificada/', data)
  return response.data
}

/**
 * Edit an existing transaction
 */
export const editarTransaccion = async (data: EditarTransaccionRequest) => {
  const response = await api.patch<EditarTransaccionResponse>('/mi-caja/editar-transaccion/', data)
  return response.data
}

/**
 * Delete a transaction (with mandatory reason)
 */
export const eliminarTransaccion = async (data: EliminarTransaccionRequest) => {
  const response = await api.post<EliminarTransaccionResponse>('/mi-caja/eliminar-transaccion/', data)
  return response.data
}

// ==================== TRANSACTION QUERIES ====================

export const getMisTransacciones = async (fecha?: string, payment_method?: string) => {
  const params: any = {}
  if (fecha) params.fecha = fecha
  if (payment_method) params.payment_method = payment_method

  const response = await api.get<MisTransaccionesResponse>('/mi-caja/mis-transacciones/', { params })
  return response.data
}

export const getResumenDia = async (fecha?: string) => {
  const params: any = {}
  if (fecha) params.fecha = fecha

  const response = await api.get<ResumenDiario>('/mi-caja/resumen-dia/', { params })
  return response.data
}

export const getTurnosPendientesCobro = async () => {
  const response = await api.get<TurnosPendientesResponse>('/mi-caja/turnos-pendientes-cobro/')
  return response.data
}

// ==================== CASH REGISTER CLOSING ====================

export const cerrarCaja = async (data: CierreCajaRequest) => {
  const response = await api.post<CierreCajaResponse>('/mi-caja/cierre-caja/', data)
  return response.data
}
