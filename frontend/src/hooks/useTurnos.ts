import { useState } from 'react'
import api from '../services/api'
import type { Turno, TurnoList, TurnoDetail } from '../types/models'

interface UseTurnosReturn {
  turnos: TurnoList[]
  loading: boolean
  error: string | null
  fetchTurnos: (params?: FetchTurnosParams) => Promise<void>
  fetchTurno: (id: number) => Promise<TurnoDetail | null>
  createTurno: (data: Partial<Turno>) => Promise<Turno | null>
  updateTurno: (id: number, data: Partial<Turno>) => Promise<Turno | null>
  deleteTurno: (id: number) => Promise<boolean>
  fetchTurnosHoy: () => Promise<TurnoList[]>
  fetchTurnosProximos: () => Promise<TurnoList[]>
  verificarDisponibilidad: (data: DisponibilidadData) => Promise<DisponibilidadResponse>
  cambiarEstado: (id: number, estado: string) => Promise<Turno | null>
}

interface FetchTurnosParams {
  fecha_desde?: string
  fecha_hasta?: string
  profesional?: number
  cliente?: number
  servicio?: number
  estado?: string
  estado_pago?: string
  search?: string
}

interface DisponibilidadData {
  profesional: number
  fecha_hora_inicio: string
  fecha_hora_fin: string
  turno_id?: number
}

interface DisponibilidadResponse {
  disponible: boolean
  conflictos?: Array<{
    id: number
    fecha_hora_inicio: string
    fecha_hora_fin: string
    cliente: string
    servicio: string
  }>
}

export const useTurnos = (): UseTurnosReturn => {
  const [turnos, setTurnos] = useState<TurnoList[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const cleanTurnoData = (data: Partial<Turno>) => {
    const cleaned: any = { ...data }
    const optionalFields = ['profesional', 'notas', 'monto_sena', 'fecha_hora_fin', 'monto_total']

    optionalFields.forEach(field => {
      if (cleaned[field] === '' || cleaned[field] === undefined || cleaned[field] === null) {
        delete cleaned[field]
      }
    })

    return cleaned
  }

  const fetchTurnos = async (params?: FetchTurnosParams) => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get('/turnos/turnos/', { params })
      // Manejar respuesta paginada o array directo
      const data = Array.isArray(response.data) ? response.data : response.data.results || []
      setTurnos(data)
    } catch (err: any) {
      setError(err.response?.data?.message || 'Error al cargar los turnos')
      console.error('Error fetching turnos:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchTurno = async (id: number): Promise<TurnoDetail | null> => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get(`/turnos/turnos/${id}/`)
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.message || 'Error al cargar el turno')
      console.error('Error fetching turno:', err)
      return null
    } finally {
      setLoading(false)
    }
  }

  const createTurno = async (data: Partial<Turno>): Promise<Turno | null> => {
    setLoading(true)
    setError(null)
    try {
      const cleanedData = cleanTurnoData(data)
      console.log('Sending turno data:', cleanedData)
      const response = await api.post('/turnos/turnos/', cleanedData)
      await fetchTurnos()
      return response.data
    } catch (err: any) {
      console.error('Full error response:', JSON.stringify(err.response?.data, null, 2))

      // Construir mensaje de error detallado
      let errorMessage = 'Error al crear el turno:\n'
      const errors = err.response?.data

      if (errors) {
        Object.keys(errors).forEach(key => {
          const value = errors[key]
          const message = Array.isArray(value) ? value.join(', ') : value
          errorMessage += `${key}: ${message}\n`
        })
      }

      setError(errorMessage)
      console.error('Error creating turno:', err)
      throw err
    } finally {
      setLoading(false)
    }
  }

  const updateTurno = async (id: number, data: Partial<Turno>): Promise<Turno | null> => {
    setLoading(true)
    setError(null)
    try {
      const cleanedData = cleanTurnoData(data)
      const response = await api.put(`/turnos/turnos/${id}/`, cleanedData)
      await fetchTurnos()
      return response.data
    } catch (err: any) {
      const errorMessage = err.response?.data?.fecha_hora_inicio?.[0] ||
                          err.response?.data?.message ||
                          'Error al actualizar el turno'
      setError(errorMessage)
      console.error('Error updating turno:', err)
      throw err
    } finally {
      setLoading(false)
    }
  }

  const deleteTurno = async (id: number): Promise<boolean> => {
    setLoading(true)
    setError(null)
    try {
      await api.delete(`/turnos/turnos/${id}/`)
      await fetchTurnos()
      return true
    } catch (err: any) {
      setError(err.response?.data?.message || 'Error al eliminar el turno')
      console.error('Error deleting turno:', err)
      return false
    } finally {
      setLoading(false)
    }
  }

  const fetchTurnosHoy = async (): Promise<TurnoList[]> => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get('/turnos/turnos/hoy/')
      const data = Array.isArray(response.data) ? response.data : response.data.results || []
      setTurnos(data)
      return data
    } catch (err: any) {
      setError(err.response?.data?.message || 'Error al cargar los turnos de hoy')
      console.error('Error fetching turnos hoy:', err)
      return []
    } finally {
      setLoading(false)
    }
  }

  const fetchTurnosProximos = async (): Promise<TurnoList[]> => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get('/turnos/turnos/proximos/')
      const data = Array.isArray(response.data) ? response.data : response.data.results || []
      setTurnos(data)
      return data
    } catch (err: any) {
      setError(err.response?.data?.message || 'Error al cargar los próximos turnos')
      console.error('Error fetching turnos proximos:', err)
      return []
    } finally {
      setLoading(false)
    }
  }

  const verificarDisponibilidad = async (data: DisponibilidadData): Promise<DisponibilidadResponse> => {
    try {
      const response = await api.post('/turnos/turnos/verificar_disponibilidad/', data)
      return response.data
    } catch (err: any) {
      console.error('Error verificando disponibilidad:', err)
      return { disponible: false }
    }
  }

  const cambiarEstado = async (id: number, estado: string): Promise<Turno | null> => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.post(`/turnos/turnos/${id}/cambiar_estado/`, { estado })
      await fetchTurnos()
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.error || 'Error al cambiar el estado')
      console.error('Error cambiando estado:', err)
      return null
    } finally {
      setLoading(false)
    }
  }

  return {
    turnos,
    loading,
    error,
    fetchTurnos,
    fetchTurno,
    createTurno,
    updateTurno,
    deleteTurno,
    fetchTurnosHoy,
    fetchTurnosProximos,
    verificarDisponibilidad,
    cambiarEstado,
  }
}
