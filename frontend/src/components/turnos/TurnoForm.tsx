import React, { useState, useEffect } from 'react'
import { Input, Select, Button, Badge } from '../ui'
import type { Turno, Cliente, Servicio, Usuario, EstadoTurno, EstadoPago, TurnoList } from '../../types/models'
import api from '../../services/api'

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

// Generar horarios de 8am a 7pm cada 30 minutos
const generateTimeSlots = () => {
  const slots = []
  for (let hour = 8; hour <= 19; hour++) {
    for (let minute = 0; minute < 60; minute += 30) {
      if (hour === 19 && minute > 0) break // Terminar a las 19:00
      const time = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`
      const label = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`
      slots.push({ value: time, label })
    }
  }
  return slots
}

const timeSlots = generateTimeSlots()

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

  useEffect(() => {
    loadFormData()
  }, [])

  useEffect(() => {
    if (initialData) {
      setFormData({ ...formData, ...initialData })
      // Si hay fecha inicial, parsearla
      if (initialData.fecha_hora_inicio) {
        const date = new Date(initialData.fecha_hora_inicio)
        setSelectedDate(date.toISOString().split('T')[0])
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

  const loadFormData = async () => {
    setLoadingData(true)
    try {
      const [clientesRes, serviciosRes, usuariosRes] = await Promise.all([
        api.get('/clientes/clientes/'),
        api.get('/servicios/servicios/?activo=true'),
        api.get('/empleados/usuarios/'),
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

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  // Verificar si un horario está ocupado (considerando duración del servicio)
  const isTimeSlotOccupied = (time: string) => {
    if (!turnosDelDia.length || !servicioSeleccionado) {
      return false
    }

    const [hours, minutes] = time.split(':').map(Number)
    const selectedDateTime = new Date(selectedDate)
    selectedDateTime.setHours(hours, minutes, 0)

    // Calcular fin del turno según duración del servicio
    const finTurno = new Date(selectedDateTime)
    finTurno.setMinutes(finTurno.getMinutes() + servicioSeleccionado.duracion_minutos)

    // Verificar si hay conflicto con algún turno existente
    const hasConflict = turnosDelDia.some(turno => {
      // Si estamos editando, excluir el turno actual de la verificación
      if (initialData?.id && turno.id === initialData.id) {
        return false
      }

      const inicioExistente = new Date(turno.fecha_hora_inicio)
      const finExistente = new Date(turno.fecha_hora_fin)

      // Hay conflicto si:
      // 1. El nuevo turno empieza durante un turno existente
      // 2. El nuevo turno termina durante un turno existente
      // 3. El nuevo turno engloba completamente un turno existente
      const conflict = (
        (selectedDateTime >= inicioExistente && selectedDateTime < finExistente) || // Empieza durante
        (finTurno > inicioExistente && finTurno <= finExistente) || // Termina durante
        (selectedDateTime <= inicioExistente && finTurno >= finExistente) // Engloba
      )

      if (conflict) {
        console.log(`Slot ${time}: OCUPADO - Conflicto con turno ${inicioExistente.toLocaleTimeString()} - ${finExistente.toLocaleTimeString()}`)
      }

      return conflict
    })

    return hasConflict
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
      // Combinar fecha y hora en formato ISO
      const fechaHoraInicio = `${selectedDate}T${selectedTime}:00`
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

  const handleTimeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedTime(e.target.value)
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
        <Select
          label="Cliente"
          name="cliente"
          value={formData.cliente?.toString() || ''}
          onChange={handleChange}
          options={clienteOptions}
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
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-md">
          <p className="text-sm text-blue-800">
            <strong>Duración:</strong> {servicioSeleccionado.duracion_minutos} minutos |
            <strong> Precio:</strong> ${servicioSeleccionado.precio}
          </p>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="fecha" className="block text-sm font-medium text-gray-700 mb-1">
            Fecha <span className="text-red-500">*</span>
          </label>
          <input
            type="date"
            id="fecha"
            value={selectedDate}
            onChange={handleDateChange}
            min={new Date().toISOString().split('T')[0]}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>

        <div>
          <label htmlFor="hora" className="block text-sm font-medium text-gray-700 mb-1">
            Hora (8am - 7pm) <span className="text-red-500">*</span>
          </label>
          <select
            id="hora"
            value={selectedTime}
            onChange={handleTimeChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          >
            <option value="">Seleccionar hora</option>
            {timeSlots.map(slot => (
              <option
                key={slot.value}
                value={slot.value}
                disabled={isTimeSlotOccupied(slot.value)}
              >
                {slot.label} {isTimeSlotOccupied(slot.value) ? '(Ocupado)' : ''}
              </option>
            ))}
          </select>
          {errors.fecha_hora_inicio && (
            <p className="mt-1 text-sm text-red-600">{errors.fecha_hora_inicio}</p>
          )}
          {selectedDate && (!formData.servicio || !formData.profesional) && (
            <p className="mt-1 text-sm text-blue-600">
              💡 Selecciona servicio y profesional para ver disponibilidad
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
