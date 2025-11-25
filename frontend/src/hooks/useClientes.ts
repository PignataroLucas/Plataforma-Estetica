import { useState, useCallback } from 'react'
import api from '@/services/api'
import toast from 'react-hot-toast'
import { Cliente, PaginatedResponse } from '@/types/models'

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
      const response = await api.get<PaginatedResponse<Cliente>>('/clientes/list/')
      setClientes(response.data.results)
      return response.data.results
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Error al cargar clientes'
      setError(errorMsg)
      toast.error(errorMsg)
      setClientes([]) // Asegurar que clientes sea un array vacío en caso de error
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
      const response = await api.get<Cliente>(`/clientes/list/${id}/`)
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
   * Limpiar datos del formulario antes de enviar
   * Elimina campos vacíos para que el backend use valores por defecto
   */
  const cleanClienteData = (data: Partial<Cliente>) => {
    const cleaned: any = { ...data }

    // Campos opcionales que se deben eliminar si están vacíos
    const optionalFields = ['email', 'fecha_nacimiento', 'telefono_alternativo', 'direccion',
                            'ciudad', 'provincia', 'codigo_postal', 'numero_documento',
                            'alergias', 'contraindicaciones', 'notas_medicas', 'preferencias',
                            'tipo_documento', 'foto']

    // Eliminar campos que están vacíos, undefined o null
    optionalFields.forEach(field => {
      if (cleaned[field] === '' || cleaned[field] === undefined || cleaned[field] === null) {
        delete cleaned[field]
      }
    })

    return cleaned
  }

  /**
   * Crear un nuevo cliente
   */
  const createCliente = useCallback(async (data: Partial<Cliente>) => {
    setLoading(true)
    setError(null)
    try {
      const cleanedData = cleanClienteData(data)
      const response = await api.post<Cliente>('/clientes/list/', cleanedData)
      setClientes(prev => [...prev, response.data])
      toast.success('Cliente creado exitosamente')
      return response.data
    } catch (err: any) {
      // Intentar obtener el mensaje de error más específico del backend
      let errorMsg = 'Error al crear cliente'
      if (err.response?.data) {
        if (typeof err.response.data === 'string') {
          errorMsg = err.response.data
        } else if (err.response.data.detail) {
          errorMsg = err.response.data.detail
        } else {
          // Si hay errores de validación por campo
          const firstError = Object.values(err.response.data)[0]
          if (Array.isArray(firstError)) {
            errorMsg = firstError[0]
          }
        }
      }
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
      const cleanedData = cleanClienteData(data)
      const response = await api.patch<Cliente>(`/clientes/list/${id}/`, cleanedData)
      setClientes(prev =>
        prev.map(cliente => cliente.id === id ? response.data : cliente)
      )
      toast.success('Cliente actualizado exitosamente')
      return response.data
    } catch (err: any) {
      // Intentar obtener el mensaje de error más específico del backend
      let errorMsg = 'Error al actualizar cliente'
      if (err.response?.data) {
        if (typeof err.response.data === 'string') {
          errorMsg = err.response.data
        } else if (err.response.data.detail) {
          errorMsg = err.response.data.detail
        } else {
          // Si hay errores de validación por campo
          const firstError = Object.values(err.response.data)[0]
          if (Array.isArray(firstError)) {
            errorMsg = firstError[0]
          }
        }
      }
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
      await api.delete(`/clientes/list/${id}/`)
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
      const response = await api.get<PaginatedResponse<Cliente>>('/clientes/list/', {
        params: { search: query }
      })
      setClientes(response.data.results)
      return response.data.results
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Error al buscar clientes'
      setError(errorMsg)
      toast.error(errorMsg)
      setClientes([]) // Asegurar que clientes sea un array vacío en caso de error
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
