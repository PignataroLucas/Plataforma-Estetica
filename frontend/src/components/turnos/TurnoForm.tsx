import React, { useState, useEffect } from 'react'
import { Input, Select, Button, Badge, DateInput } from '../ui'
import SearchSelect from '../ui/SearchSelect/SearchSelect'
import type { Turno, Cliente, Servicio, Usuario, EstadoTurno, EstadoPago, TurnoList } from '../../types/models'
import api from '../../services/api'
import { getTodayForInput, formatDateForInput } from '../../utils/dateUtils'

interface TurnoFormProps {
  initialData?: Partial<Turno>
  onSubmit: (data: Partial<Turno>) => void
  onCancel: () => void
  submitLabel?: string
  formId?: string
  showButtons?: boolean
}

const estadoTurnoOptions = [
  { value: 'PENDIENTE', label: 'Pendiente' },
  { value: 'CONFIRMADO', label: 'Confirmado' },
  { value: 'COMPLETADO', label: 'Completado' },
  { value: 'CANCELADO', label: 'Cancelado' },
  { value: 'NO_SHOW', label: 'No Show' },
]

const estadoPagoOptions = [
  { value: 'PENDIENTE', label: 'Pendiente' },
  { value: 'CON_SENA', label: 'Con Seña' },
  { value: 'PAGADO', label: 'Pagado' },
]

export const TurnoForm: React.FC<TurnoFormProps> = ({
  initialData,
  onSubmit,
  onCancel,
  submitLabel = 'Guardar',
  formId = 'turno-form',
  showButtons = false,
}) => {
  const [formData, setFormData] = useState<Partial<Turno>>({
    estado: 'CONFIRMADO' as EstadoTurno,
    estado_pago: 'PENDIENTE' as EstadoPago,
    ...initialData,
  })

  const [selectedDate, setSelectedDate] = useState('')
  const [selectedTime, setSelectedTime] = useState('')
  const [errors, setErrors] = useState<Partial<Record<keyof Turno, string>>>({})
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [servicios, setServicios] = useState<Servicio[]>([])
  const [profesionales, setProfesionales] = useState<Usuario[]>([])
  const [loadingData, setLoadingData] = useState(true)
  const [turnosDelDia, setTurnosDelDia] = useState<TurnoList[]>([])
  const [loadingTurnos, setLoadingTurnos] = useState(false)

  // Estado para validar horario laboral del profesional
  const [loadingSlots, setLoadingSlots] = useState(false)
  const [horarioLaboral, setHorarioLaboral] = useState<{ inicio: string; fin: string } | null>(null)
  const [diaNoLaboral, setDiaNoLaboral] = useState(false)

  useEffect(() => {
    loadFormData()
  }, [])

  useEffect(() => {
    if (initialData) {
      setFormData({ ...formData, ...initialData })
      // Si hay fecha inicial, parsearla
      if (initialData.fecha_hora_inicio) {
        const date = new Date(initialData.fecha_hora_inicio)
        setSelectedDate(formatDateForInput(date))
        setSelectedTime(`${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`)
      }
    }
  }, [initialData])

  // Cargar turnos del día cuando cambie la fecha, profesional o servicio
  useEffect(() => {
    if (selectedDate && formData.profesional) {
      loadTurnosDelDia()
    }
  }, [selectedDate, formData.profesional, formData.servicio])

  // Cargar horario laboral del profesional cuando cambie fecha, profesional o servicio
  useEffect(() => {
    if (selectedDate && formData.profesional && formData.servicio) {
      loadHorariosDisponibles()
    } else {
      setDiaNoLaboral(false)
      setHorarioLaboral(null)
    }
  }, [selectedDate, formData.profesional, formData.servicio])

  const loadTurnosDelDia = async () => {
    if (!selectedDate) return

    setLoadingTurnos(true)
    try {
      const response = await api.get('/turnos/turnos/', {
        params: {
          fecha_desde: `${selectedDate}T00:00:00`,
          fecha_hasta: `${selectedDate}T23:59:59`,
          profesional: formData.profesional,
        }
      })
      const allData = Array.isArray(response.data) ? response.data : response.data.results || []

      // Filtrar solo turnos confirmados y pendientes (los que realmente ocupan el horario)
      const filteredData = allData.filter((turno: TurnoList) =>
        turno.estado === 'CONFIRMADO' || turno.estado === 'PENDIENTE'
      )

      console.log('Turnos del día cargados:', filteredData)
      setTurnosDelDia(filteredData)
    } catch (err) {
      console.error('Error loading turnos del día:', err)
      setTurnosDelDia([])
    } finally {
      setLoadingTurnos(false)
    }
  }

  const loadHorariosDisponibles = async () => {
    if (!selectedDate || !formData.profesional || !formData.servicio) return

    setLoadingSlots(true)
    setDiaNoLaboral(false)

    try {
      const response = await api.get(`/empleados/usuarios/${formData.profesional}/horarios_disponibles/`, {
        params: {
          fecha: selectedDate,
          servicio_id: formData.servicio,
        }
      })

      if (response.data.disponible === false) {
        setDiaNoLaboral(true)
        setHorarioLaboral(null)
      } else {
        setDiaNoLaboral(false)
        setHorarioLaboral(response.data.horario_laboral || null)
      }
    } catch (err) {
      console.error('Error loading horarios disponibles:', err)
      setHorarioLaboral(null)
      setDiaNoLaboral(false)
    } finally {
      setLoadingSlots(false)
    }
  }

  const loadFormData = async () => {
    setLoadingData(true)
    try {
      const [clientesRes, serviciosRes, usuariosRes] = await Promise.all([
        api.get('/clientes/clientes/', { params: { page_size: 1000 } }),
        api.get('/servicios/servicios/', { params: { activo: true, page_size: 1000 } }),
        api.get('/empleados/usuarios/', { params: { page_size: 1000 } }),
      ])

      // Manejar respuestas paginadas o arrays directos
      const clientesData = Array.isArray(clientesRes.data) ? clientesRes.data : clientesRes.data.results || []
      const serviciosData = Array.isArray(serviciosRes.data) ? serviciosRes.data : serviciosRes.data.results || []
      const usuariosData = Array.isArray(usuariosRes.data) ? usuariosRes.data : usuariosRes.data.results || []

      setClientes(clientesData)
      setServicios(serviciosData)
      setProfesionales(usuariosData.filter((u: Usuario) => u.activo))
    } catch (err) {
      console.error('Error loading form data:', err)
    } finally {
      setLoadingData(false)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
    if (errors[name as keyof Turno]) {
      setErrors(prev => ({ ...prev, [name]: undefined }))
    }
  }

  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof Turno, string>> = {}

    if (!formData.cliente) {
      newErrors.cliente = 'El cliente es requerido'
    }
    if (!formData.servicio) {
      newErrors.servicio = 'El servicio es requerido'
    }
    if (!selectedDate) {
      newErrors.fecha_hora_inicio = 'La fecha es requerida'
    }
    if (!selectedTime) {
      newErrors.fecha_hora_inicio = 'La hora es requerida'
    }
    if (selectedTime && servicioSeleccionado && isTimeSlotOccupied(selectedTime)) {
      newErrors.fecha_hora_inicio = 'Ese horario solapa con un turno existente'
    }
    if (selectedTime && horarioLaboral && servicioSeleccionado && !isWithinWorkingHours(selectedTime)) {
      newErrors.fecha_hora_inicio = `Fuera del horario laboral (${horarioLaboral.inicio} - ${horarioLaboral.fin})`
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const isTimeSlotOccupied = (time: string) => {
    if (!turnosDelDia.length || !servicioSeleccionado) {
      return false
    }

    const [hours, minutes] = time.split(':').map(Number)
    const selectedDateTime = new Date(selectedDate)
    selectedDateTime.setHours(hours, minutes, 0)

    const finTurno = new Date(selectedDateTime)
    finTurno.setMinutes(finTurno.getMinutes() + servicioSeleccionado.duracion_minutos)

    return turnosDelDia.some(turno => {
      if (initialData?.id && turno.id === initialData.id) {
        return false
      }
      const inicioExistente = new Date(turno.fecha_hora_inicio)
      const finExistente = new Date(turno.fecha_hora_fin)
      return (
        (selectedDateTime >= inicioExistente && selectedDateTime < finExistente) ||
        (finTurno > inicioExistente && finTurno <= finExistente) ||
        (selectedDateTime <= inicioExistente && finTurno >= finExistente)
      )
    })
  }

  const isWithinWorkingHours = (time: string) => {
    if (!horarioLaboral || !servicioSeleccionado) return true
    const [h, m] = time.split(':').map(Number)
    const endTotal = h * 60 + m + servicioSeleccionado.duracion_minutos
    const endH = Math.floor(endTotal / 60)
    const endM = endTotal % 60
    const endStr = `${endH.toString().padStart(2, '0')}:${endM.toString().padStart(2, '0')}`
    return time >= horarioLaboral.inicio && endStr <= horarioLaboral.fin
  }

  // Obtener el servicio seleccionado para calcular duración
  const servicioSeleccionado = servicios.find(s => s.id === formData.servicio)

  const formatTime = (dateString: string) => {
    const date = new Date(dateString)
    return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (validateForm()) {
      // Incluir timezone de Argentina en formato ISO
      const fechaHoraInicio = `${selectedDate}T${selectedTime}:00-03:00`
      const submitData = {
        ...formData,
        fecha_hora_inicio: fechaHoraInicio
      }
      onSubmit(submitData)
    }
  }

  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedDate(e.target.value)
  }

  const handleTimeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value
    let digits = raw.replace(/\D/g, '').slice(0, 4)

    if (digits.length >= 1) {
      const firstTwo = digits.slice(0, 2)
      const hh = parseInt(firstTwo, 10)
      if (digits.length === 1 && hh > 2) {
        digits = '0' + digits
      } else if (digits.length >= 2 && hh > 23) {
        digits = '23' + digits.slice(2)
      }
    }
    if (digits.length >= 3) {
      const mm = parseInt(digits.slice(2, 4).padEnd(2, '0'), 10)
      if (mm > 59) {
        digits = digits.slice(0, 2) + '59'
      }
    }

    let formatted = digits
    if (digits.length > 2) {
      formatted = `${digits.slice(0, 2)}:${digits.slice(2)}`
    }

    setSelectedTime(formatted)
    if (errors.fecha_hora_inicio) {
      setErrors(prev => ({ ...prev, fecha_hora_inicio: undefined }))
    }
  }

  const clienteOptions = clientes.map(c => ({
    value: c.id.toString(),
    label: `${c.nombre} ${c.apellido} - ${c.telefono}`,
  }))

  const servicioOptions = servicios.map(s => ({
    value: s.id.toString(),
    label: `${s.nombre} - $${s.precio} (${s.duracion_minutos} min)`,
  }))

  const profesionalOptions = [
    { value: '', label: 'Sin asignar' },
    ...profesionales.map(p => ({
      value: p.id.toString(),
      label: `${p.first_name} ${p.last_name}`.trim() || p.username,
    })),
  ]

  if (loadingData) {
    return <div className="p-4 text-center">Cargando datos del formulario...</div>
  }

  return (
    <form id={formId} onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <SearchSelect
          label="Cliente"
          value={formData.cliente?.toString() || ''}
          onChange={(val) => setFormData(prev => ({ ...prev, cliente: val ? parseInt(val) : undefined }))}
          options={clienteOptions}
          placeholder="Buscar cliente..."
          required
          error={errors.cliente}
        />

        <Select
          label="Servicio"
          name="servicio"
          value={formData.servicio?.toString() || ''}
          onChange={handleChange}
          options={servicioOptions}
          required
          error={errors.servicio}
        />
      </div>

      <Select
        label="Profesional"
        name="profesional"
        value={formData.profesional?.toString() || ''}
        onChange={handleChange}
        options={profesionalOptions}
      />

      {servicioSeleccionado && (
        <div className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="text-2xl">⏱️</span>
                <div>
                  <p className="text-xs text-gray-600 font-medium">Duración</p>
                  <p className="text-sm font-bold text-blue-800">{servicioSeleccionado.duracion_minutos} min</p>
                </div>
              </div>
              <div className="h-8 w-px bg-blue-200"></div>
              <div className="flex items-center gap-2">
                <span className="text-2xl">💰</span>
                <div>
                  <p className="text-xs text-gray-600 font-medium">Precio</p>
                  <p className="text-sm font-bold text-blue-800">${servicioSeleccionado.precio}</p>
                </div>
              </div>
            </div>
            {loadingSlots && (
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                <span>Buscando horarios...</span>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <DateInput
          label="Fecha"
          value={selectedDate}
          onChange={(value) => handleDateChange({ target: { value } } as React.ChangeEvent<HTMLInputElement>)}
          min={getTodayForInput()}
          required
        />

        <div>
          <label htmlFor="hora" className="block text-sm font-medium text-gray-700 mb-1">
            Hora {horarioLaboral && `(${horarioLaboral.inicio} - ${horarioLaboral.fin})`} <span className="text-red-500">*</span>
          </label>
          <input
            id="hora"
            type="text"
            value={selectedTime}
            onChange={handleTimeChange}
            placeholder="HH:MM"
            maxLength={5}
            inputMode="numeric"
            pattern="^([01][0-9]|2[0-3]):[0-5][0-9]$"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
            disabled={diaNoLaboral}
          />
          {errors.fecha_hora_inicio && (
            <p className="mt-1 text-sm text-red-600">{errors.fecha_hora_inicio}</p>
          )}
          {!errors.fecha_hora_inicio && diaNoLaboral && (
            <p className="mt-1 text-sm text-amber-600">
              ⚠️ El profesional no trabaja en este día
            </p>
          )}
          {!errors.fecha_hora_inicio && loadingSlots && (
            <p className="mt-1 text-sm text-gray-500">
              🔄 Verificando horario laboral...
            </p>
          )}
          {!errors.fecha_hora_inicio && selectedDate && (!formData.servicio || !formData.profesional) && (
            <p className="mt-1 text-sm text-blue-600">
              💡 Seleccioná servicio y profesional para validar disponibilidad
            </p>
          )}
          {!errors.fecha_hora_inicio && selectedTime && servicioSeleccionado && isTimeSlotOccupied(selectedTime) && (
            <p className="mt-1 text-sm text-red-600">
              ⛔ Ese horario solapa con un turno existente
            </p>
          )}
          {!errors.fecha_hora_inicio && selectedTime && horarioLaboral && servicioSeleccionado && !isTimeSlotOccupied(selectedTime) && !isWithinWorkingHours(selectedTime) && (
            <p className="mt-1 text-sm text-amber-600">
              ⚠️ Fuera del horario laboral del profesional
            </p>
          )}
        </div>
      </div>

      {/* Mostrar turnos ocupados del día */}
      {selectedDate && formData.profesional && turnosDelDia.length > 0 && (
        <div className="p-4 bg-gray-50 border border-gray-200 rounded-md">
          <h4 className="text-sm font-semibold text-gray-700 mb-2">
            Turnos ocupados este día:
          </h4>
          <div className="space-y-1">
            {turnosDelDia.map(turno => (
              <div key={turno.id} className="text-sm text-gray-600 flex items-center gap-2">
                <Badge variant="warning" className="text-xs">
                  {formatTime(turno.fecha_hora_inicio)} - {formatTime(turno.fecha_hora_fin)}
                </Badge>
                <span>{turno.cliente_nombre} - {turno.servicio_nombre}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {loadingTurnos && (
        <div className="text-sm text-gray-500">Cargando turnos disponibles...</div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <Select
          label="Estado"
          name="estado"
          value={formData.estado || 'CONFIRMADO'}
          onChange={handleChange}
          options={estadoTurnoOptions}
          required
        />

        <Select
          label="Estado de Pago"
          name="estado_pago"
          value={formData.estado_pago || 'PENDIENTE'}
          onChange={handleChange}
          options={estadoPagoOptions}
          required
        />
      </div>

      <Input
        label="Seña"
        type="number"
        name="monto_sena"
        value={formData.monto_sena?.toString() || ''}
        onChange={handleChange}
        min="0"
        step="0.01"
        placeholder="Opcional"
      />

      <div>
        <label htmlFor="notas" className="block text-sm font-medium text-gray-700 mb-1">
          Notas
        </label>
        <textarea
          id="notas"
          name="notas"
          value={formData.notas || ''}
          onChange={handleChange}
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Observaciones adicionales..."
        />
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
