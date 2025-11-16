import { useCallback, useMemo } from 'react'
import { Calendar, momentLocalizer, Event, SlotInfo } from 'react-big-calendar'
import moment from 'moment'
import 'moment/locale/es'
import 'react-big-calendar/lib/css/react-big-calendar.css'
import type { TurnoList } from '../../types/models'

// Configurar moment en español
moment.locale('es')
const localizer = momentLocalizer(moment)

interface CalendarViewProps {
  turnos: TurnoList[]
  onSelectEvent: (turno: TurnoList) => void
  onSelectSlot: (slotInfo: { start: Date; end: Date }) => void
  loading?: boolean
}

// Extender el tipo Event para incluir nuestros datos
interface TurnoEvent extends Event {
  turno: TurnoList
}

// Función para obtener color según el estado del turno
const getEventColor = (estado: string): string => {
  switch (estado) {
    case 'CONFIRMADO':
      return '#10b981' // green-500
    case 'PENDIENTE':
      return '#f59e0b' // amber-500
    case 'COMPLETADO':
      return '#3b82f6' // blue-500
    case 'CANCELADO':
      return '#ef4444' // red-500
    case 'NO_SHOW':
      return '#6b7280' // gray-500
    default:
      return '#8b5cf6' // violet-500
  }
}

// Mensajes en español para el calendario
const messages = {
  allDay: 'Todo el día',
  previous: '←',
  next: '→',
  today: 'Hoy',
  month: 'Mes',
  week: 'Semana',
  day: 'Día',
  agenda: 'Agenda',
  date: 'Fecha',
  time: 'Hora',
  event: 'Turno',
  noEventsInRange: 'No hay turnos en este rango',
  showMore: (total: number) => `+ Ver más (${total})`,
}

export const CalendarView: React.FC<CalendarViewProps> = ({
  turnos,
  onSelectEvent,
  onSelectSlot,
  loading,
}) => {
  // Convertir turnos a eventos del calendario
  const events: TurnoEvent[] = useMemo(() => {
    return turnos.map(turno => ({
      title: `${turno.cliente_nombre} - ${turno.servicio_nombre}`,
      start: new Date(turno.fecha_hora_inicio),
      end: new Date(turno.fecha_hora_fin),
      resource: turno.profesional_nombre || 'Sin asignar',
      turno,
    }))
  }, [turnos])

  // Handler para cuando se hace click en un evento
  const handleSelectEvent = useCallback(
    (event: TurnoEvent) => {
      onSelectEvent(event.turno)
    },
    [onSelectEvent]
  )

  // Handler para cuando se hace click en un slot vacío
  const handleSelectSlot = useCallback(
    (slotInfo: SlotInfo) => {
      onSelectSlot({
        start: slotInfo.start as Date,
        end: slotInfo.end as Date,
      })
    },
    [onSelectSlot]
  )

  // Personalizar el estilo de cada evento
  const eventStyleGetter = useCallback((event: TurnoEvent) => {
    const backgroundColor = getEventColor(event.turno.estado)

    return {
      style: {
        backgroundColor,
        borderRadius: '4px',
        opacity: 0.9,
        color: 'white',
        border: 'none',
        display: 'block',
        fontSize: '0.875rem',
        padding: '2px 5px',
      },
    }
  }, [])

  // Formato personalizado para mostrar los eventos
  const EventComponent = ({ event }: { event: TurnoEvent }) => {
    const turno = event.turno
    return (
      <div className="text-xs">
        <strong>{turno.cliente_nombre}</strong>
        <div>{turno.servicio_nombre}</div>
        {turno.profesional_nombre && (
          <div className="text-white/80">{turno.profesional_nombre}</div>
        )}
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 bg-white rounded-lg">
        <div className="text-center">
          <div className="text-gray-500">Cargando calendario...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg p-4" style={{ height: '700px' }}>
      <Calendar
        localizer={localizer}
        events={events}
        startAccessor="start"
        endAccessor="end"
        messages={messages}
        onSelectEvent={handleSelectEvent}
        onSelectSlot={handleSelectSlot}
        selectable
        eventPropGetter={eventStyleGetter}
        components={{
          event: EventComponent,
        }}
        defaultView="week"
        views={['day', 'week', 'month']}
        step={30}
        timeslots={1}
        min={new Date(2025, 0, 1, 8, 0, 0)} // 8:00 AM
        max={new Date(2025, 0, 1, 19, 0, 0)} // 7:00 PM
        className="turnos-calendar"
        popup
        culture="es"
      />
    </div>
  )
}
