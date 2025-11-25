import api from './api'
import type { Cliente, PlanTratamiento, RutinaCuidado, NotaCliente, PaginatedResponse } from '@/types/models'

/**
 * Cliente Services - API calls for patient tracking system
 */

// ==================== CLIENTES ====================

export const getClientes = async (params?: any) => {
  const response = await api.get<PaginatedResponse<Cliente>>('/clientes/list/', { params })
  return response.data
}

export const getCliente = async (id: number) => {
  const response = await api.get<Cliente>(`/clientes/list/${id}/`)
  return response.data
}

export const createCliente = async (data: Partial<Cliente>) => {
  const response = await api.post<Cliente>('/clientes/list/', data)
  return response.data
}

export const updateCliente = async (id: number, data: Partial<Cliente>) => {
  const response = await api.patch<Cliente>(`/clientes/list/${id}/`, data)
  return response.data
}

export const deleteCliente = async (id: number) => {
  await api.delete(`/clientes/list/${id}/`)
}

// ==================== PLANES DE TRATAMIENTO ====================

export const getPlanesTratamiento = async (clienteId?: number) => {
  const params = clienteId ? { cliente: clienteId } : {}
  const response = await api.get<PaginatedResponse<PlanTratamiento>>('/clientes/planes-tratamiento/', { params })
  return response.data
}

export const getPlanTratamiento = async (id: number) => {
  const response = await api.get<PlanTratamiento>(`/clientes/planes-tratamiento/${id}/`)
  return response.data
}

export const createPlanTratamiento = async (data: Partial<PlanTratamiento>) => {
  const response = await api.post<PlanTratamiento>('/clientes/planes-tratamiento/', data)
  return response.data
}

export const updatePlanTratamiento = async (id: number, data: Partial<PlanTratamiento>) => {
  const response = await api.patch<PlanTratamiento>(`/clientes/planes-tratamiento/${id}/`, data)
  return response.data
}

export const deletePlanTratamiento = async (id: number) => {
  await api.delete(`/clientes/planes-tratamiento/${id}/`)
}

// ==================== RUTINAS DE CUIDADO ====================

export const getRutinasCuidado = async (clienteId?: number, activa?: boolean) => {
  const params: any = {}
  if (clienteId) params.cliente = clienteId
  if (activa !== undefined) params.activa = activa

  const response = await api.get<PaginatedResponse<RutinaCuidado>>('/clientes/rutinas-cuidado/', { params })
  return response.data
}

export const getRutinaCuidado = async (id: number) => {
  const response = await api.get<RutinaCuidado>(`/clientes/rutinas-cuidado/${id}/`)
  return response.data
}

export const createRutinaCuidado = async (data: Partial<RutinaCuidado>) => {
  const response = await api.post<RutinaCuidado>('/clientes/rutinas-cuidado/', data)
  return response.data
}

export const updateRutinaCuidado = async (id: number, data: Partial<RutinaCuidado>) => {
  const response = await api.patch<RutinaCuidado>(`/clientes/rutinas-cuidado/${id}/`, data)
  return response.data
}

export const deleteRutinaCuidado = async (id: number) => {
  await api.delete(`/clientes/rutinas-cuidado/${id}/`)
}

// ==================== NOTAS DE CLIENTE ====================

export const getNotasCliente = async (clienteId?: number, destacada?: boolean) => {
  const params: any = {}
  if (clienteId) params.cliente = clienteId
  if (destacada !== undefined) params.destacada = destacada

  const response = await api.get<PaginatedResponse<NotaCliente>>('/clientes/notas-cliente/', { params })
  return response.data
}

export const getNotaCliente = async (id: number) => {
  const response = await api.get<NotaCliente>(`/clientes/notas-cliente/${id}/`)
  return response.data
}

export const createNotaCliente = async (data: Partial<NotaCliente>) => {
  const response = await api.post<NotaCliente>('/clientes/notas-cliente/', data)
  return response.data
}

export const updateNotaCliente = async (id: number, data: Partial<NotaCliente>) => {
  const response = await api.patch<NotaCliente>(`/clientes/notas-cliente/${id}/`, data)
  return response.data
}

export const deleteNotaCliente = async (id: number) => {
  await api.delete(`/clientes/notas-cliente/${id}/`)
}
