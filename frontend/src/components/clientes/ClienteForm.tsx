import { useState, FormEvent, ChangeEvent, useEffect } from 'react'
import { Cliente } from '@/types/models'
import { Button, Input, Select } from '@/components/ui'

/**
 * ClienteForm - Formulario de Cliente (Create/Edit)
 * Aplica principios SOLID:
 * - SRP: Solo maneja el formulario de cliente
 * - DIP: Recibe callbacks como props, no depende de implementaciones concretas
 * - OCP: Extensible via props
 */

interface ClienteFormProps {
  cliente?: Cliente | null
  onSubmit: (data: Partial<Cliente>) => Promise<void>
  onCancel: () => void
  loading?: boolean
  formId?: string
  showButtons?: boolean
}

export default function ClienteForm({
  cliente,
  onSubmit,
  onCancel,
  loading = false,
  formId = 'cliente-form',
  showButtons = true,
}: ClienteFormProps) {
  const [formData, setFormData] = useState<Partial<Cliente>>({
    nombre: '',
    apellido: '',
    email: '',
    telefono: '',
    telefono_alternativo: '',
    fecha_nacimiento: '',
    direccion: '',
    ciudad: '',
    provincia: '',
    codigo_postal: '',
    tipo_documento: 'DNI',
    numero_documento: '',
    alergias: '',
    contraindicaciones: '',
    notas_medicas: '',
    preferencias: '',
    acepta_promociones: true,
    acepta_whatsapp: true,
  })

  const [errors, setErrors] = useState<Partial<Record<keyof Cliente, string>>>({})

  // Cargar datos del cliente si estamos editando
  useEffect(() => {
    if (cliente) {
      setFormData({
        nombre: cliente.nombre,
        apellido: cliente.apellido,
        email: cliente.email,
        telefono: cliente.telefono,
        telefono_alternativo: cliente.telefono_alternativo,
        fecha_nacimiento: cliente.fecha_nacimiento,
        direccion: cliente.direccion,
        ciudad: cliente.ciudad,
        provincia: cliente.provincia,
        codigo_postal: cliente.codigo_postal,
        tipo_documento: cliente.tipo_documento,
        numero_documento: cliente.numero_documento,
        alergias: cliente.alergias,
        contraindicaciones: cliente.contraindicaciones,
        notas_medicas: cliente.notas_medicas,
        preferencias: cliente.preferencias,
        acepta_promociones: cliente.acepta_promociones,
        acepta_whatsapp: cliente.acepta_whatsapp,
      })
    }
  }, [cliente])

  /**
   * Validación del formulario (SRP)
   */
  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof Cliente, string>> = {}

    if (!formData.nombre?.trim()) {
      newErrors.nombre = 'El nombre es requerido'
    }

    if (!formData.apellido?.trim()) {
      newErrors.apellido = 'El apellido es requerido'
    }

    // Email es opcional, pero si se ingresa debe ser válido
    if (formData.email?.trim() && !/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email inválido'
    }

    if (!formData.telefono?.trim()) {
      newErrors.telefono = 'El teléfono es requerido'
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
  const handleChange = (e: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target
    const checked = (e.target as HTMLInputElement).checked

    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }))

    // Limpiar error del campo al escribir
    if (errors[name as keyof Cliente]) {
      setErrors(prev => ({
        ...prev,
        [name]: undefined,
      }))
    }
  }

  return (
    <form id={formId} onSubmit={handleSubmit} className="space-y-6">
      {/* Datos Personales */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Datos Personales
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="Nombre"
            name="nombre"
            value={formData.nombre}
            onChange={handleChange}
            error={errors.nombre}
            required
            fullWidth
          />

          <Input
            label="Apellido"
            name="apellido"
            value={formData.apellido}
            onChange={handleChange}
            error={errors.apellido}
            required
            fullWidth
          />

          <Input
            label="Email"
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            error={errors.email}
            fullWidth
            placeholder="correo@ejemplo.com"
          />

          <Input
            label="Fecha de Nacimiento"
            type="date"
            name="fecha_nacimiento"
            value={formData.fecha_nacimiento}
            onChange={handleChange}
            fullWidth
          />
        </div>
      </div>

      {/* Contacto */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Información de Contacto
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="Teléfono Principal"
            name="telefono"
            value={formData.telefono}
            onChange={handleChange}
            error={errors.telefono}
            required
            fullWidth
            placeholder="ej: +54 9 11 1234-5678"
          />

          <Input
            label="Teléfono Alternativo"
            name="telefono_alternativo"
            value={formData.telefono_alternativo}
            onChange={handleChange}
            fullWidth
            placeholder="Opcional"
          />

          <Input
            label="Dirección"
            name="direccion"
            value={formData.direccion}
            onChange={handleChange}
            fullWidth
            className="md:col-span-2"
          />

          <Input
            label="Ciudad"
            name="ciudad"
            value={formData.ciudad}
            onChange={handleChange}
            fullWidth
          />

          <Input
            label="Provincia"
            name="provincia"
            value={formData.provincia}
            onChange={handleChange}
            fullWidth
          />

          <Input
            label="Código Postal"
            name="codigo_postal"
            value={formData.codigo_postal}
            onChange={handleChange}
            fullWidth
          />
        </div>
      </div>

      {/* Información Médica */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Información Médica
        </h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Alergias
            </label>
            <textarea
              name="alergias"
              value={formData.alergias}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              rows={2}
              placeholder="Ej: Polen, frutos secos, látex..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Contraindicaciones
            </label>
            <textarea
              name="contraindicaciones"
              value={formData.contraindicaciones}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              rows={2}
              placeholder="Ej: Embarazo, marcapasos, problemas cardíacos..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Notas Médicas
            </label>
            <textarea
              name="notas_medicas"
              value={formData.notas_medicas}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              rows={2}
              placeholder="Información médica adicional relevante..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Preferencias
            </label>
            <textarea
              name="preferencias"
              value={formData.preferencias}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              rows={2}
              placeholder="Ej: Prefiere turnos por la mañana, aceites esenciales de lavanda..."
            />
          </div>
        </div>
      </div>

      {/* Configuración de Comunicación */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Configuración de Comunicación
        </h3>
        <div className="space-y-3">
          <label className="flex items-center">
            <input
              type="checkbox"
              name="acepta_promociones"
              checked={formData.acepta_promociones}
              onChange={handleChange}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
            />
            <span className="ml-2 text-sm text-gray-700">
              Acepta recibir promociones y novedades
            </span>
          </label>

          <label className="flex items-center">
            <input
              type="checkbox"
              name="acepta_whatsapp"
              checked={formData.acepta_whatsapp}
              onChange={handleChange}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
            />
            <span className="ml-2 text-sm text-gray-700">
              Acepta notificaciones por WhatsApp
            </span>
          </label>
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
            {cliente ? 'Actualizar Cliente' : 'Crear Cliente'}
          </Button>
        </div>
      )}
    </form>
  )
}
