import axios from 'axios'
import { useAuthStore } from '@/stores/authStore'
import type {
  MensajeTemplate,
  MensajeTemplateList,
  TipoMensaje,
  VariablesDisponibles,
} from '@/types/models'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().accessToken
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // If error is 401 and we haven't retried yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = useAuthStore.getState().refreshToken
        const response = await axios.post(`${API_URL}/auth/refresh/`, {
          refresh: refreshToken,
        })

        const { access } = response.data
        useAuthStore.getState().updateToken(access)

        originalRequest.headers.Authorization = `Bearer ${access}`
        return api(originalRequest)
      } catch (refreshError) {
        // Refresh token is invalid, logout user
        useAuthStore.getState().logout()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

// API methods for Mensajes Templates
export const mensajesTemplatesApi = {
  // Listar templates
  list: () => api.get<MensajeTemplateList[]>('/notificaciones/mensajes-templates/'),

  // Obtener template por ID
  get: (id: number) => api.get<MensajeTemplate>(`/notificaciones/mensajes-templates/${id}/`),

  // Crear nuevo template
  create: (data: Partial<MensajeTemplate>) =>
    api.post<MensajeTemplate>('/notificaciones/mensajes-templates/', data),

  // Actualizar template
  update: (id: number, data: Partial<MensajeTemplate>) =>
    api.put<MensajeTemplate>(`/notificaciones/mensajes-templates/${id}/`, data),

  // Actualizar parcialmente template
  patch: (id: number, data: Partial<MensajeTemplate>) =>
    api.patch<MensajeTemplate>(`/notificaciones/mensajes-templates/${id}/`, data),

  // Eliminar template
  delete: (id: number) => api.delete(`/notificaciones/mensajes-templates/${id}/`),

  // Restaurar defaults (todos o uno específico)
  resetDefaults: (tipo?: TipoMensaje) =>
    api.post('/notificaciones/mensajes-templates/reset_defaults/', tipo ? { tipo } : {}),

  // Obtener variables disponibles
  variablesDisponibles: () =>
    api.get<VariablesDisponibles>('/notificaciones/mensajes-templates/variables_disponibles/'),
}

export default api
