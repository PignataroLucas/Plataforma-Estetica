import { useState, FormEvent, ChangeEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import api from '@/services/api'
import toast from 'react-hot-toast'
import { LoginFormData, LoginResponse } from '@/types/models'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card } from '@/components/ui/Card'

/**
 * LoginPage - Container Component (Lógica + Presentación)
 * Aplica principios SOLID:
 * - SRP: Solo maneja login
 * - DIP: Depende de abstracciones (useAuthStore, api)
 * - OCP: Usa componentes reutilizables
 */
export default function LoginPage() {
  const navigate = useNavigate()
  const setAuth = useAuthStore((state) => state.setAuth)
  const [formData, setFormData] = useState<LoginFormData>({
    username: '',
    password: '',
  })
  const [errors, setErrors] = useState<Partial<LoginFormData>>({})
  const [loading, setLoading] = useState(false)

  /**
   * Validación del formulario (SRP - responsabilidad única)
   */
  const validateForm = (): boolean => {
    const newErrors: Partial<LoginFormData> = {}

    if (!formData.username.trim()) {
      newErrors.username = 'El usuario es requerido'
    }

    if (!formData.password) {
      newErrors.password = 'La contraseña es requerida'
    } else if (formData.password.length < 6) {
      newErrors.password = 'La contraseña debe tener al menos 6 caracteres'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  /**
   * Handler del submit (SRP - responsabilidad única)
   */
  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    setLoading(true)
    setErrors({})

    try {
      const response = await api.post<LoginResponse>('/auth/login/', formData)
      const { access, refresh, user } = response.data

      setAuth(user, access, refresh)
      toast.success('Inicio de sesión exitoso')
      navigate('/')
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail ||
                          error.response?.data?.message ||
                          'Error al iniciar sesión. Verifica tus credenciales.'
      toast.error(errorMessage)
      setErrors({ password: 'Usuario o contraseña incorrectos' })
    } finally {
      setLoading(false)
    }
  }

  /**
   * Handler de cambios en inputs (SRP - responsabilidad única)
   */
  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }))
    // Limpiar error del campo al escribir
    if (errors[name as keyof LoginFormData]) {
      setErrors(prev => ({
        ...prev,
        [name]: undefined,
      }))
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-primary-100 px-4">
      <Card className="w-full max-w-md" padding="lg">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-primary-600 mb-2">
            Plataforma Estética
          </h1>
          <p className="text-gray-600">
            Inicia sesión para gestionar tu centro
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Usuario"
            type="text"
            id="username"
            name="username"
            value={formData.username}
            onChange={handleChange}
            error={errors.username}
            fullWidth
            required
            autoComplete="username"
            placeholder="Ingresa tu usuario"
          />

          <Input
            label="Contraseña"
            type="password"
            id="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            error={errors.password}
            fullWidth
            required
            autoComplete="current-password"
            placeholder="Ingresa tu contraseña"
          />

          <Button
            type="submit"
            variant="primary"
            size="lg"
            fullWidth
            loading={loading}
          >
            Iniciar Sesión
          </Button>
        </form>

        {/* Footer */}
        <p className="text-xs text-gray-500 text-center mt-6">
          Plataforma Estética v1.0 - {new Date().getFullYear()}
        </p>
      </Card>
    </div>
  )
}
