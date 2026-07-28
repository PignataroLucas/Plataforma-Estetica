import { useState, FormEvent, ChangeEvent, useEffect } from 'react'
import { Servicio, MaquinaAlquilada, PaginatedResponse, DIAS_SEMANA } from '@/types/models'
import { Button, Input } from '@/components/ui'
import api from '@/services/api'

/**
 * ServicioForm - Formulario de Servicio (Create/Edit)
 * Aplica principios SOLID:
 * - SRP: Solo maneja el formulario de servicio
 * - DIP: Recibe callbacks como props, no depende de implementaciones concretas
 * - OCP: Extensible via props
 */

interface TextareaProps {
  id: string
  name: string
  label: string
  value: string
  onChange: (e: ChangeEvent<HTMLTextAreaElement>) => void
  rows?: number
  placeholder?: string
  helper?: string
}

/**
 * El Input de ui/ solo renderiza <input>. Los textos largos de la ficha necesitan
 * varias líneas, así que va este textarea con el mismo look del resto del form.
 */
function Textarea({ id, name, label, value, onChange, rows = 4, placeholder, helper }: TextareaProps) {
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      <textarea
        id={id}
        name={name}
        value={value}
        onChange={onChange}
        rows={rows}
        placeholder={placeholder}
        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
      />
      {helper && <p className="mt-1 text-xs text-gray-500">{helper}</p>}
    </div>
  )
}

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
    maquina_alquilada: undefined,
    reservable_por_cliente: false,
    dias_reserva: [],
    descripcion: '',
    beneficios: '',
    video_url: '',
  })

  const [errors, setErrors] = useState<Partial<Record<keyof Servicio, string>>>({})
  const [maquinas, setMaquinas] = useState<MaquinaAlquilada[]>([])
  const [loadingMaquinas, setLoadingMaquinas] = useState(false)

  // Cargar máquinas al montar
  useEffect(() => {
    const fetchMaquinas = async () => {
      setLoadingMaquinas(true)
      try {
        const response = await api.get<PaginatedResponse<MaquinaAlquilada>>('/servicios/maquinas/')
        // Handle paginated response
        const maquinasList = response.data && 'results' in response.data
          ? response.data.results
          : response.data as any
        setMaquinas(maquinasList.filter((m: MaquinaAlquilada) => m.activa))
      } catch (error) {
        console.error('Error loading machines:', error)
      } finally {
        setLoadingMaquinas(false)
      }
    }
    fetchMaquinas()
  }, [])

  // Cargar datos del servicio si estamos editando
  useEffect(() => {
    if (servicio) {
      setFormData({
        nombre: servicio.nombre,
        duracion_minutos: servicio.duracion_minutos,
        precio: servicio.precio,
        maquina_alquilada: servicio.maquina_alquilada,
        reservable_por_cliente: servicio.reservable_por_cliente ?? false,
        dias_reserva: servicio.dias_reserva ?? [],
        descripcion: servicio.descripcion ?? '',
        beneficios: servicio.beneficios ?? '',
        video_url: servicio.video_url ?? '',
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

    // El backend valida la URL igual (URLField); acá evitamos el viaje de ida y vuelta.
    const video = formData.video_url?.trim()
    if (video && !/^https?:\/\/.+\..+/i.test(video)) {
      newErrors.video_url = 'Pegá el link completo, empezando con https://'
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
  const handleChange = (
    e: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
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

  /**
   * Handler del check "reservable desde la app".
   * Al desactivarlo limpiamos los días propios: si mañana se vuelve a activar,
   * arranca con la regla general en vez de arrastrar una configuración vieja.
   */
  const handleReservableChange = (e: ChangeEvent<HTMLInputElement>) => {
    const checked = e.target.checked
    setFormData(prev => ({
      ...prev,
      reservable_por_cliente: checked,
      dias_reserva: checked ? prev.dias_reserva ?? [] : [],
    }))
  }

  /**
   * Agrega o saca un día de la lista de días propios del servicio
   */
  const toggleDiaReserva = (dia: string) => {
    setFormData(prev => {
      const actuales = prev.dias_reserva ?? []
      return {
        ...prev,
        dias_reserva: actuales.includes(dia)
          ? actuales.filter(d => d !== dia)
          : [...actuales, dia],
      }
    })
  }

  /**
   * Handler para cambio de máquina
   */
  const handleMachineChange = (e: ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value
    setFormData(prev => ({
      ...prev,
      maquina_alquilada: value ? parseInt(value) : undefined,
    }))
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

          {/* Selector de Máquina */}
          <div>
            <label htmlFor="maquina_alquilada" className="block text-sm font-medium text-gray-700 mb-1">
              Máquina Alquilada (Opcional)
            </label>
            <select
              id="maquina_alquilada"
              name="maquina_alquilada"
              value={formData.maquina_alquilada || ''}
              onChange={handleMachineChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loadingMaquinas}
            >
              <option value="">Sin máquina</option>
              {maquinas.map(maquina => (
                <option key={maquina.id} value={maquina.id}>
                  {maquina.nombre} - ${maquina.costo_diario.toLocaleString()}/día
                </option>
              ))}
            </select>
            <p className="mt-1 text-xs text-gray-500">
              Selecciona si este servicio requiere una máquina alquilada. El costo se cobrará una vez por día.
            </p>
          </div>

          {/* Reserva desde la app del cliente */}
          <div className="border-t border-gray-200 pt-4">
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                name="reservable_por_cliente"
                checked={formData.reservable_por_cliente ?? false}
                onChange={handleReservableChange}
                className="mt-0.5 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm">
                <span className="font-medium text-gray-900">
                  El cliente puede reservarlo desde la app
                </span>
                <span className="block text-xs text-gray-500 mt-0.5">
                  Activalo solo para los servicios que el centro puede preparar de un día
                  para el otro. Desde el CRM lo podés agendar siempre, sin importar esta opción.
                </span>
              </span>
            </label>

            {formData.reservable_por_cliente && (
              <div className="mt-3 ml-7">
                <p className="text-sm font-medium text-gray-700 mb-1">Días para reservar</p>
                <p className="text-xs text-gray-500 mb-2">
                  Si no elegís ninguno, se usan los días generales de la app (lunes a jueves).
                  Los días que elijas acá <strong>reemplazan</strong> esa regla.
                </p>
                <div className="flex flex-wrap gap-2">
                  {DIAS_SEMANA.map(dia => {
                    const activo = (formData.dias_reserva ?? []).includes(dia.valor)
                    return (
                      <button
                        key={dia.valor}
                        type="button"
                        onClick={() => toggleDiaReserva(dia.valor)}
                        className={`px-3 py-1.5 text-sm rounded-md border transition-colors ${
                          activo
                            ? 'bg-blue-600 border-blue-600 text-white'
                            : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                        }`}
                      >
                        {dia.label}
                      </button>
                    )
                  })}
                </div>
                {(formData.dias_reserva ?? []).length === 0 && (
                  <p className="mt-2 text-xs text-gray-500">
                    Usando los días generales: lunes a jueves.
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Aviso sobre análisis de profit */}
          {formData.maquina_alquilada && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
              <div className="flex items-start gap-2">
                <svg className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div className="text-sm text-amber-800">
                  <p className="font-medium">Máquina alquilada por día</p>
                  <p className="mt-1">El análisis de rentabilidad se verá en <strong>Finanzas</strong> considerando todos los turnos del día.</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Ficha para la app del cliente */}
      <div className="border-t border-gray-200 pt-6">
        <h3 className="text-lg font-semibold text-gray-900">Ficha para la app</h3>
        <p className="mt-1 mb-4 text-sm text-gray-500">
          Lo que la clienta ve cuando toca el tratamiento en la app. Si dejás algo vacío,
          esa parte no se muestra.
        </p>
        <div className="space-y-4">
          <Textarea
            id="descripcion"
            name="descripcion"
            label="Qué es"
            value={formData.descripcion ?? ''}
            onChange={handleChange}
            rows={4}
            placeholder="Contale en qué consiste el tratamiento, cómo es la sesión, qué se siente."
            helper="Es el texto principal de la ficha."
          />

          <Textarea
            id="beneficios"
            name="beneficios"
            label="Beneficios"
            value={formData.beneficios ?? ''}
            onChange={handleChange}
            rows={4}
            placeholder={'Un beneficio por línea. Ej:\nRedefine el óvalo facial\nMejora la textura de la piel'}
            helper="Escribí uno por línea: en la app se muestran como lista."
          />

          <Input
            label="Link del video (opcional)"
            name="video_url"
            type="url"
            value={formData.video_url ?? ''}
            onChange={handleChange}
            error={errors.video_url}
            fullWidth
            placeholder="https://www.instagram.com/reel/..."
          />
          <p className="-mt-3 text-xs text-gray-500">
            Pegá el link del posteo de Instagram, YouTube o TikTok. Se abre desde la ficha.
          </p>
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
