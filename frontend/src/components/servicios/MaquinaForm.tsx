import { useState, FormEvent, ChangeEvent, useEffect } from 'react'
import { MaquinaAlquilada } from '@/types/models'
import { Button, Input } from '@/components/ui'

interface MaquinaFormProps {
  maquina?: MaquinaAlquilada | null
  onSubmit: (data: Partial<MaquinaAlquilada>) => Promise<void>
  onCancel: () => void
  loading?: boolean
  formId?: string
  showButtons?: boolean
}

export default function MaquinaForm({
  maquina,
  onSubmit,
  onCancel,
  loading = false,
  formId = 'maquina-form',
  showButtons = true,
}: MaquinaFormProps) {
  const [formData, setFormData] = useState<Partial<MaquinaAlquilada>>({
    nombre: '',
    descripcion: '',
    costo_diario: 0,
    proveedor: '',
    activa: true,
  })

  const [errors, setErrors] = useState<Partial<Record<keyof MaquinaAlquilada, string>>>({})

  // Cargar datos de la máquina si estamos editando
  useEffect(() => {
    if (maquina) {
      setFormData({
        nombre: maquina.nombre,
        descripcion: maquina.descripcion,
        costo_diario: maquina.costo_diario,
        proveedor: maquina.proveedor,
        activa: maquina.activa,
      })
    }
  }, [maquina])

  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof MaquinaAlquilada, string>> = {}

    if (!formData.nombre?.trim()) {
      newErrors.nombre = 'El nombre es requerido'
    }

    if (!formData.costo_diario || formData.costo_diario <= 0) {
      newErrors.costo_diario = 'El costo diario debe ser mayor a 0'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    await onSubmit(formData)
  }

  const handleChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target
    const checked = (e.target as HTMLInputElement).checked

    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? parseFloat(value) || 0 : type === 'checkbox' ? checked : value,
    }))

    if (errors[name as keyof MaquinaAlquilada]) {
      setErrors(prev => ({
        ...prev,
        [name]: undefined,
      }))
    }
  }

  return (
    <form id={formId} onSubmit={handleSubmit} className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Información de la Máquina
        </h3>
        <div className="space-y-4">
          <Input
            label="Nombre de la Máquina"
            name="nombre"
            value={formData.nombre}
            onChange={handleChange}
            error={errors.nombre}
            required
            fullWidth
            placeholder="Ej: Liposonix Pro, Criolipolisis X2000"
          />

          <div>
            <label htmlFor="descripcion" className="block text-sm font-medium text-gray-700 mb-1">
              Descripción
            </label>
            <textarea
              id="descripcion"
              name="descripcion"
              value={formData.descripcion}
              onChange={handleChange}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Detalles técnicos, especificaciones..."
            />
          </div>

          <Input
            label="Costo Diario ($)"
            type="number"
            name="costo_diario"
            value={formData.costo_diario?.toString() || ''}
            onChange={handleChange}
            error={errors.costo_diario}
            required
            fullWidth
            placeholder="Ej: 80000"
            min="0"
            step="0.01"
          />

          <Input
            label="Proveedor"
            name="proveedor"
            value={formData.proveedor}
            onChange={handleChange}
            fullWidth
            placeholder="Ej: MedEquip SA, Estética Tech"
          />

          <div className="flex items-center">
            <input
              type="checkbox"
              id="activa"
              name="activa"
              checked={formData.activa}
              onChange={handleChange}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="activa" className="ml-2 block text-sm text-gray-900">
              Máquina activa
            </label>
          </div>
        </div>
      </div>

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
            {maquina ? 'Actualizar Máquina' : 'Crear Máquina'}
          </Button>
        </div>
      )}
    </form>
  )
}
