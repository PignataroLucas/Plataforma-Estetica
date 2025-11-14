import { useState } from 'react'
import api from '../services/api'
import type { Usuario } from '../types/models'

interface UseEmpleadosReturn {
  empleados: Usuario[]
  loading: boolean
  error: string | null
  fetchEmpleados: (params?: FetchEmpleadosParams) => Promise<void>
  fetchEmpleado: (id: number) => Promise<Usuario | null>
  createEmpleado: (data: EmpleadoFormData) => Promise<Usuario | null>
  updateEmpleado: (id: number, data: Partial<Usuario>) => Promise<Usuario | null>
  deleteEmpleado: (id: number) => Promise<boolean>
  cambiarEstado: (id: number, activo: boolean) => Promise<Usuario | null>
}

interface FetchEmpleadosParams {
  rol?: string
  activo?: boolean
  sucursal?: number
  search?: string
}

interface EmpleadoFormData {
  username: string
  email: string
  password: string
  password2: string
  first_name: string
  last_name: string
  telefono?: string
  fecha_nacimiento?: string
  direccion?: string
  rol: string
  fecha_ingreso?: string
  especialidades?: string
  activo: boolean
  sucursal?: number
}

export const useEmpleados = (): UseEmpleadosReturn => {
  const [empleados, setEmpleados] = useState<Usuario[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const cleanEmpleadoData = (data: Partial<Usuario> | EmpleadoFormData) => {
    const cleaned: any = { ...data }
    const optionalFields = ['telefono', 'fecha_nacimiento', 'direccion', 'fecha_ingreso',
                            'especialidades', 'sucursal', 'foto']

    optionalFields.forEach(field => {
      if (cleaned[field] === '' || cleaned[field] === undefined || cleaned[field] === null) {
        delete cleaned[field]
      }
    })

    return cleaned
  }

  const fetchEmpleados = async (params?: FetchEmpleadosParams) => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get('/empleados/usuarios/', { params })
      const data = Array.isArray(response.data) ? response.data : response.data.results || []
      setEmpleados(data)
    } catch (err: any) {
      setError(err.response?.data?.message || 'Error al cargar los empleados')
      console.error('Error fetching empleados:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchEmpleado = async (id: number): Promise<Usuario | null> => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get(`/empleados/usuarios/${id}/`)
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.message || 'Error al cargar el empleado')
      console.error('Error fetching empleado:', err)
      return null
    } finally {
      setLoading(false)
    }
  }

  const createEmpleado = async (data: EmpleadoFormData): Promise<Usuario | null> => {
    setLoading(true)
    setError(null)
    try {
      const cleanedData = cleanEmpleadoData(data)
      console.log('Sending empleado data:', cleanedData)
      const response = await api.post('/empleados/usuarios/', cleanedData)
      await fetchEmpleados()
      return response.data
    } catch (err: any) {
      console.error('Full error response:', JSON.stringify(err.response?.data, null, 2))

      // Construir mensaje de error detallado
      let errorMessage = 'Error al crear el empleado:\n'
      const errors = err.response?.data

      if (errors) {
        Object.keys(errors).forEach(key => {
          const value = errors[key]
          const message = Array.isArray(value) ? value.join(', ') : value
          errorMessage += `${key}: ${message}\n`
        })
      }

      setError(errorMessage)
      console.error('Error creating empleado:', err)
      throw err
    } finally {
      setLoading(false)
    }
  }

  const updateEmpleado = async (id: number, data: Partial<Usuario>): Promise<Usuario | null> => {
    setLoading(true)
    setError(null)
    try {
      const cleanedData = cleanEmpleadoData(data)
      const response = await api.put(`/empleados/usuarios/${id}/`, cleanedData)
      await fetchEmpleados()
      return response.data
    } catch (err: any) {
      const errorMessage = err.response?.data?.message || 'Error al actualizar el empleado'
      setError(errorMessage)
      console.error('Error updating empleado:', err)
      throw err
    } finally {
      setLoading(false)
    }
  }

  const deleteEmpleado = async (id: number): Promise<boolean> => {
    setLoading(true)
    setError(null)
    try {
      await api.delete(`/empleados/usuarios/${id}/`)
      await fetchEmpleados()
      return true
    } catch (err: any) {
      setError(err.response?.data?.message || 'Error al eliminar el empleado')
      console.error('Error deleting empleado:', err)
      return false
    } finally {
      setLoading(false)
    }
  }

  const cambiarEstado = async (id: number, activo: boolean): Promise<Usuario | null> => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.post(`/empleados/usuarios/${id}/cambiar_estado/`, { activo })
      await fetchEmpleados()
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
    empleados,
    loading,
    error,
    fetchEmpleados,
    fetchEmpleado,
    createEmpleado,
    updateEmpleado,
    deleteEmpleado,
    cambiarEstado,
  }
}
