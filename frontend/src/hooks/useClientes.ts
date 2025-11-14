import { useState, useCallback } from 'react'
import api from '@/services/api'
import toast from 'react-hot-toast'
import { Cliente } from '@/types/models'

/**
 * useClientes Hook - Custom Hook para gestión de clientes
 * Aplica principios SOLID:
 * - SRP: Solo maneja operaciones CRUD de clientes
 * - DIP: Componentes dependen de este hook, no de axios directamente
 * - OCP: Extensible para agregar más operaciones
 */
export const useClientes = () => {
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  /**
   * Obtener todos los clientes
   */
  const fetchClientes = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get<Cliente[]>('/clientes/')
      setClientes(response.data)
      return response.data
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Error al cargar clientes'
      setError(errorMsg)
      toast.error(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * Obtener un cliente por ID
   */
  const fetchCliente = useCallback(async (id: number) => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get<Cliente>(`/clientes/${id}/`)
      return response.data
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Error al cargar cliente'
      setError(errorMsg)
      toast.error(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * Crear un nuevo cliente
   */
  const createCliente = useCallback(async (data: Partial<Cliente>) => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.post<Cliente>('/clientes/', data)
      setClientes(prev => [...prev, response.data])
      toast.success('Cliente creado exitosamente')
      return response.data
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Error al crear cliente'
      setError(errorMsg)
      toast.error(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * Actualizar un cliente existente
   */
  const updateCliente = useCallback(async (id: number, data: Partial<Cliente>) => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.patch<Cliente>(`/clientes/${id}/`, data)
      setClientes(prev =>
        prev.map(cliente => cliente.id === id ? response.data : cliente)
      )
      toast.success('Cliente actualizado exitosamente')
      return response.data
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Error al actualizar cliente'
      setError(errorMsg)
      toast.error(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * Eliminar un cliente
   */
  const deleteCliente = useCallback(async (id: number) => {
    setLoading(true)
    setError(null)
    try {
      await api.delete(`/clientes/${id}/`)
      setClientes(prev => prev.filter(cliente => cliente.id !== id))
      toast.success('Cliente eliminado exitosamente')
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Error al eliminar cliente'
      setError(errorMsg)
      toast.error(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * Buscar clientes (por nombre, email, teléfono)
   */
  const searchClientes = useCallback(async (query: string) => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get<Cliente[]>('/clientes/', {
        params: { search: query }
      })
      setClientes(response.data)
      return response.data
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Error al buscar clientes'
      setError(errorMsg)
      toast.error(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  return {
    clientes,
    loading,
    error,
    fetchClientes,
    fetchCliente,
    createCliente,
    updateCliente,
    deleteCliente,
    searchClientes,
  }
}
