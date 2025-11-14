import { useState, useCallback } from 'react'
import api from '@/services/api'
import toast from 'react-hot-toast'
import { Servicio, PaginatedResponse } from '@/types/models'

/**
 * useServicios Hook - Custom Hook para gestión de servicios
 * Aplica principios SOLID:
 * - SRP: Solo maneja operaciones CRUD de servicios
 * - DIP: Componentes dependen de este hook, no de axios directamente
 * - OCP: Extensible para agregar más operaciones
 */
export const useServicios = () => {
  const [servicios, setServicios] = useState<Servicio[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  /**
   * Limpiar datos del formulario antes de enviar
   * Elimina campos vacíos para que el backend use valores por defecto
   */
  const cleanServicioData = (data: Partial<Servicio>) => {
    const cleaned: any = { ...data }

    // Campos opcionales que se deben eliminar si están vacíos
    const optionalFields = ['descripcion', 'codigo', 'categoria', 'requiere_equipamiento',
                            'comision_porcentaje', 'color']

    // Eliminar campos que están vacíos, undefined o null
    optionalFields.forEach(field => {
      if (cleaned[field] === '' || cleaned[field] === undefined || cleaned[field] === null) {
        delete cleaned[field]
      }
    })

    return cleaned
  }

  /**
   * Obtener todos los servicios
   */
  const fetchServicios = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get<PaginatedResponse<Servicio>>('/servicios/servicios/')
      setServicios(response.data.results)
      return response.data.results
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Error al cargar servicios'
      setError(errorMsg)
      toast.error(errorMsg)
      setServicios([])
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * Obtener un servicio por ID
   */
  const fetchServicio = useCallback(async (id: number) => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get<Servicio>(`/servicios/servicios/${id}/`)
      return response.data
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Error al cargar servicio'
      setError(errorMsg)
      toast.error(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * Crear un nuevo servicio
   */
  const createServicio = useCallback(async (data: Partial<Servicio>) => {
    setLoading(true)
    setError(null)
    try {
      const cleanedData = cleanServicioData(data)
      const response = await api.post<Servicio>('/servicios/servicios/', cleanedData)
      setServicios(prev => [...prev, response.data])
      toast.success('Servicio creado exitosamente')
      return response.data
    } catch (err: any) {
      let errorMsg = 'Error al crear servicio'
      if (err.response?.data) {
        if (typeof err.response.data === 'string') {
          errorMsg = err.response.data
        } else if (err.response.data.detail) {
          errorMsg = err.response.data.detail
        } else {
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
   * Actualizar un servicio existente
   */
  const updateServicio = useCallback(async (id: number, data: Partial<Servicio>) => {
    setLoading(true)
    setError(null)
    try {
      const cleanedData = cleanServicioData(data)
      const response = await api.patch<Servicio>(`/servicios/servicios/${id}/`, cleanedData)
      setServicios(prev =>
        prev.map(servicio => servicio.id === id ? response.data : servicio)
      )
      toast.success('Servicio actualizado exitosamente')
      return response.data
    } catch (err: any) {
      let errorMsg = 'Error al actualizar servicio'
      if (err.response?.data) {
        if (typeof err.response.data === 'string') {
          errorMsg = err.response.data
        } else if (err.response.data.detail) {
          errorMsg = err.response.data.detail
        } else {
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
   * Eliminar un servicio
   */
  const deleteServicio = useCallback(async (id: number) => {
    setLoading(true)
    setError(null)
    try {
      await api.delete(`/servicios/servicios/${id}/`)
      setServicios(prev => prev.filter(servicio => servicio.id !== id))
      toast.success('Servicio eliminado exitosamente')
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Error al eliminar servicio'
      setError(errorMsg)
      toast.error(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * Buscar servicios (por nombre, descripción)
   */
  const searchServicios = useCallback(async (query: string) => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get<PaginatedResponse<Servicio>>('/servicios/servicios/', {
        params: { search: query }
      })
      setServicios(response.data.results)
      return response.data.results
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Error al buscar servicios'
      setError(errorMsg)
      toast.error(errorMsg)
      setServicios([])
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  return {
    servicios,
    loading,
    error,
    fetchServicios,
    fetchServicio,
    createServicio,
    updateServicio,
    deleteServicio,
    searchServicios,
  }
}
