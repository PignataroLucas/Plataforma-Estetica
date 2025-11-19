import React, { useState, useEffect } from 'react'
import { Input, Select, Button } from '../ui'
import type { Usuario, Rol } from '../../types/models'

interface EmpleadoFormProps {
  initialData?: Partial<Usuario>
  onSubmit: (data: any) => void
  onCancel: () => void
  submitLabel?: string
  formId?: string
  showButtons?: boolean
  isEditing?: boolean
}

const rolOptions = [
  { value: 'EMPLEADO', label: 'Empleado Básico' },
  { value: 'MANAGER', label: 'Manager' },
  { value: 'ADMIN', label: 'Administrador/Dueño' },
]

export const EmpleadoForm: React.FC<EmpleadoFormProps> = ({
  initialData,
  onSubmit,
  onCancel,
  submitLabel = 'Guardar',
  formId = 'empleado-form',
  showButtons = false,
  isEditing = false,
}) => {
  const [formData, setFormData] = useState<any>({
    username: '',
    email: '',
    password: '',
    password2: '',
    first_name: '',
    last_name: '',
    telefono: '',
    fecha_nacimiento: '',
    direccion: '',
    rol: 'EMPLEADO' as Rol,
    fecha_ingreso: '',
    especialidades: '',
    sueldo_mensual: '',
    activo: true,
    ...initialData,
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    if (initialData) {
      setFormData({ ...formData, ...initialData })
    }
  }, [initialData])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target
    const checked = (e.target as HTMLInputElement).checked

    setFormData((prev: any) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))

    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }))
    }
  }

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!formData.username?.trim()) {
      newErrors.username = 'El nombre de usuario es requerido'
    }

    if (!formData.email?.trim()) {
      newErrors.email = 'El email es requerido'
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email inválido'
    }

    // Solo validar password al crear
    if (!isEditing) {
      if (!formData.password) {
        newErrors.password = 'La contraseña es requerida'
      } else if (formData.password.length < 8) {
        newErrors.password = 'La contraseña debe tener al menos 8 caracteres'
      }

      if (!formData.password2) {
        newErrors.password2 = 'Confirme la contraseña'
      } else if (formData.password !== formData.password2) {
        newErrors.password2 = 'Las contraseñas no coinciden'
      }
    }

    if (!formData.first_name?.trim()) {
      newErrors.first_name = 'El nombre es requerido'
    }

    if (!formData.last_name?.trim()) {
      newErrors.last_name = 'El apellido es requerido'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (validateForm()) {
      onSubmit(formData)
    }
  }

  return (
    <form id={formId} onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <Input
          label="Nombre de Usuario"
          name="username"
          value={formData.username}
          onChange={handleChange}
          required
          error={errors.username}
          placeholder="usuario123"
          disabled={isEditing} // No se puede cambiar username al editar
        />

        <Input
          label="Email"
          type="email"
          name="email"
          value={formData.email}
          onChange={handleChange}
          required
          error={errors.email}
          placeholder="usuario@ejemplo.com"
        />
      </div>

      {!isEditing && (
        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Contraseña"
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            required
            error={errors.password}
            placeholder="Mínimo 8 caracteres"
          />

          <Input
            label="Confirmar Contraseña"
            type="password"
            name="password2"
            value={formData.password2}
            onChange={handleChange}
            required
            error={errors.password2}
            placeholder="Repetir contraseña"
          />
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <Input
          label="Nombre"
          name="first_name"
          value={formData.first_name}
          onChange={handleChange}
          required
          error={errors.first_name}
          placeholder="Juan"
        />

        <Input
          label="Apellido"
          name="last_name"
          value={formData.last_name}
          onChange={handleChange}
          required
          error={errors.last_name}
          placeholder="Pérez"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Input
          label="Teléfono"
          name="telefono"
          value={formData.telefono}
          onChange={handleChange}
          placeholder="+54 11 1234-5678"
        />

        <Input
          label="Fecha de Nacimiento"
          type="date"
          name="fecha_nacimiento"
          value={formData.fecha_nacimiento}
          onChange={handleChange}
        />
      </div>

      <Input
        label="Dirección"
        name="direccion"
        value={formData.direccion}
        onChange={handleChange}
        placeholder="Calle Falsa 123, Ciudad"
      />

      <div className="grid grid-cols-2 gap-4">
        <Select
          label="Rol"
          name="rol"
          value={formData.rol}
          onChange={handleChange}
          options={rolOptions}
          required
        />

        <Input
          label="Fecha de Ingreso"
          type="date"
          name="fecha_ingreso"
          value={formData.fecha_ingreso}
          onChange={handleChange}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Input
          label="Sueldo Mensual"
          type="number"
          name="sueldo_mensual"
          value={formData.sueldo_mensual}
          onChange={handleChange}
          placeholder="0.00"
          min="0"
          step="0.01"
        />
        <div className="flex items-end">
          <p className="text-sm text-gray-500 pb-2">
            Este sueldo se usará para generar gastos mensuales en Finanzas
          </p>
        </div>
      </div>

      <div>
        <label htmlFor="especialidades" className="block text-sm font-medium text-gray-700 mb-1">
          Especialidades
        </label>
        <textarea
          id="especialidades"
          name="especialidades"
          value={formData.especialidades}
          onChange={handleChange}
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Ej: Masajes relajantes, Depilación láser, Tratamientos faciales..."
        />
      </div>

      <div className="flex items-center">
        <input
          type="checkbox"
          id="activo"
          name="activo"
          checked={formData.activo}
          onChange={handleChange}
          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
        />
        <label htmlFor="activo" className="ml-2 block text-sm text-gray-900">
          Empleado activo
        </label>
      </div>

      {showButtons && (
        <div className="flex justify-end gap-2 pt-4">
          <Button type="button" variant="secondary" onClick={onCancel}>
            Cancelar
          </Button>
          <Button type="submit" variant="primary">
            {submitLabel}
          </Button>
        </div>
      )}
    </form>
  )
}
