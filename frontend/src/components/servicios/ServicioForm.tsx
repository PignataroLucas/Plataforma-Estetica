import { useState, FormEvent, ChangeEvent, useEffect } from 'react'
import { Servicio } from '@/types/models'
import { Button, Input } from '@/components/ui'

/**
 * ServicioForm - Formulario de Servicio (Create/Edit)
 * Aplica principios SOLID:
 * - SRP: Solo maneja el formulario de servicio
 * - DIP: Recibe callbacks como props, no depende de implementaciones concretas
 * - OCP: Extensible via props
 */

interface ServicioFormProps {
  servicio?: Servicio | null
  onSubmit: (data: Partial<Servicio>) => Promise<void>
  onCancel: () => void
  loading?: boolean
  formId?: string
  showButtons?: boolean
}

export default function ServicioForm({
  servicio,
  onSubmit,
  onCancel,
  loading = false,
  formId = 'servicio-form',
  showButtons = true,
}: ServicioFormProps) {
  const [formData, setFormData] = useState<Partial<Servicio>>({
    nombre: '',
    duracion_minutos: 0,
    precio: 0,
  })

  const [errors, setErrors] = useState<Partial<Record<keyof Servicio, string>>>({})

  // Cargar datos del servicio si estamos editando
  useEffect(() => {
    if (servicio) {
      setFormData({
        nombre: servicio.nombre,
        duracion_minutos: servicio.duracion_minutos,
        precio: servicio.precio,
      })
    }
  }, [servicio])

  /**
   * Validación del formulario (SRP)
   */
  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof Servicio, string>> = {}

    if (!formData.nombre?.trim()) {
      newErrors.nombre = 'El nombre es requerido'
    }

    if (!formData.duracion_minutos || formData.duracion_minutos <= 0) {
      newErrors.duracion_minutos = 'La duración debe ser mayor a 0'
    }

    if (!formData.precio || formData.precio <= 0) {
      newErrors.precio = 'El precio debe ser mayor a 0'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  /**
   * Handler del submit (SRP)
   */
  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    await onSubmit(formData)
  }

  /**
   * Handler de cambios en inputs (SRP)
   */
  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, value, type } = e.target

    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? parseFloat(value) || 0 : value,
    }))

    // Limpiar error del campo al escribir
    if (errors[name as keyof Servicio]) {
      setErrors(prev => ({
        ...prev,
        [name]: undefined,
      }))
    }
  }

  return (
    <form id={formId} onSubmit={handleSubmit} className="space-y-6">
      {/* Información del Servicio */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Información del Servicio
        </h3>
        <div className="space-y-4">
          <Input
            label="Nombre del Servicio"
            name="nombre"
            value={formData.nombre}
            onChange={handleChange}
            error={errors.nombre}
            required
            fullWidth
            placeholder="Ej: Masaje Relajante, Limpieza Facial"
          />

          <Input
            label="Duración (minutos)"
            type="number"
            name="duracion_minutos"
            value={formData.duracion_minutos?.toString() || ''}
            onChange={handleChange}
            error={errors.duracion_minutos}
            required
            fullWidth
            placeholder="Ej: 60"
            min="1"
          />

          <Input
            label="Precio"
            type="number"
            name="precio"
            value={formData.precio?.toString() || ''}
            onChange={handleChange}
            error={errors.precio}
            required
            fullWidth
            placeholder="Ej: 5000"
            min="0"
            step="0.01"
          />
        </div>
      </div>

      {/* Botones de Acción */}
      {showButtons && (
        <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
          <Button
            type="button"
            variant="secondary"
            onClick={onCancel}
            disabled={loading}
          >
            Cancelar
          </Button>
          <Button
            type="submit"
            variant="primary"
            loading={loading}
          >
            {servicio ? 'Actualizar Servicio' : 'Crear Servicio'}
          </Button>
        </div>
      )}
    </form>
  )
}
