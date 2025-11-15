import React from 'react'
import { Table, Badge, Button } from '../ui'
import type { TurnoList } from '../../types/models'

interface TurnosListProps {
  turnos: TurnoList[]
  onEdit: (turno: TurnoList) => void
  onDelete: (turno: TurnoList) => void
  onQuickAction: (turnoId: number, newEstado: string) => void
  loading?: boolean
}

const getEstadoBadgeVariant = (estado: string): 'success' | 'warning' | 'danger' | 'info' | 'gray' => {
  switch (estado) {
    case 'CONFIRMADO':
      return 'success'
    case 'PENDIENTE':
      return 'warning'
    case 'COMPLETADO':
      return 'info'
    case 'CANCELADO':
    case 'NO_SHOW':
      return 'danger'
    default:
      return 'gray'
  }
}

const getEstadoPagoBadgeVariant = (estado: string): 'success' | 'warning' | 'danger' | 'info' | 'gray' => {
  switch (estado) {
    case 'PAGADO':
      return 'success'
    case 'CON_SENA':
      return 'warning'
    case 'PENDIENTE':
      return 'danger'
    default:
      return 'gray'
  }
}

const formatDateTime = (dateString: string) => {
  const date = new Date(dateString)
  const dateStr = date.toLocaleDateString('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
  const timeStr = date.toLocaleTimeString('es-AR', {
    hour: '2-digit',
    minute: '2-digit',
  })
  return { date: dateStr, time: timeStr }
}

const formatPrice = (price: number) => {
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
    minimumFractionDigits: 0,
  }).format(price)
}

const formatDuration = (minutes: number) => {
  if (minutes < 60) return `${minutes} min`
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  if (remainingMinutes === 0) return `${hours}h`
  return `${hours}h ${remainingMinutes}min`
}

const getEstadoLabel = (estado: string) => {
  const labels: Record<string, string> = {
    PENDIENTE: 'Pendiente',
    CONFIRMADO: 'Confirmado',
    COMPLETADO: 'Completado',
    CANCELADO: 'Cancelado',
    NO_SHOW: 'No Show',
  }
  return labels[estado] || estado
}

const getEstadoPagoLabel = (estado: string) => {
  const labels: Record<string, string> = {
    PENDIENTE: 'Pendiente',
    CON_SENA: 'Con Seña',
    PAGADO: 'Pagado',
  }
  return labels[estado] || estado
}

export const TurnosList: React.FC<TurnosListProps> = ({ turnos, onEdit, onDelete, onQuickAction, loading }) => {
  const columns = [
    {
      key: 'fecha_hora_inicio',
      header: 'Fecha',
      accessor: (turno: TurnoList) => {
        const { date, time } = formatDateTime(turno.fecha_hora_inicio)
        return (
          <div className="flex flex-col">
            <span className="font-medium">{date}</span>
            <span className="text-sm text-gray-600">{time}</span>
          </div>
        )
      },
    },
    {
      key: 'cliente_nombre',
      header: 'Cliente',
    },
    {
      key: 'servicio_nombre',
      header: 'Servicio',
      accessor: (turno: TurnoList) => (
        <div className="flex flex-col">
          <span className="font-medium">{turno.servicio_nombre}</span>
          <span className="text-sm text-gray-600">{formatDuration(turno.duracion_minutos)}</span>
        </div>
      ),
    },
    {
      key: 'profesional_nombre',
      header: 'Profesional',
      accessor: (turno: TurnoList) => turno.profesional_nombre || <span className="text-gray-400 italic">Sin asignar</span>,
    },
    {
      key: 'estado',
      header: 'Estado',
      accessor: (turno: TurnoList) => (
        <Badge variant={getEstadoBadgeVariant(turno.estado)}>
          {getEstadoLabel(turno.estado)}
        </Badge>
      ),
    },
    {
      key: 'estado_pago',
      header: 'Pago',
      accessor: (turno: TurnoList) => (
        <Badge variant={getEstadoPagoBadgeVariant(turno.estado_pago)}>
          {getEstadoPagoLabel(turno.estado_pago)}
        </Badge>
      ),
    },
    {
      key: 'monto_total',
      header: 'Monto',
      accessor: (turno: TurnoList) => <span className="font-semibold">{formatPrice(turno.monto_total)}</span>,
    },
    {
      key: 'acciones',
      header: 'Acciones',
      accessor: (turno: TurnoList) => {
        const isFinalized = ['COMPLETADO', 'CANCELADO', 'NO_SHOW'].includes(turno.estado)

        return (
          <div className="flex gap-1 flex-wrap">
            {/* Botones de acción rápida solo para turnos activos */}
            {!isFinalized && (
              <>
                <Button
                  variant="success"
                  size="sm"
                  onClick={() => onQuickAction(turno.id, 'COMPLETADO')}
                  title="Marcar como completado"
                >
                  ✅
                </Button>
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => onQuickAction(turno.id, 'CANCELADO')}
                  title="Cancelar turno"
                >
                  ❌
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => onQuickAction(turno.id, 'NO_SHOW')}
                  title="Marcar como No Show"
                >
                  🚫
                </Button>
              </>
            )}

            {/* Botones de editar/eliminar siempre disponibles */}
            <Button
              variant="secondary"
              size="sm"
              onClick={() => onEdit(turno)}
              title="Editar"
            >
              ✏️
            </Button>
            <Button
              variant="danger"
              size="sm"
              onClick={() => onDelete(turno)}
              title="Eliminar"
            >
              🗑️
            </Button>
          </div>
        )
      },
    },
  ]

  if (loading) {
    return <div className="text-center py-8">Cargando turnos...</div>
  }

  if (turnos.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No hay turnos registrados. Crea el primero usando el botón "Nuevo Turno".
      </div>
    )
  }

  return <Table columns={columns} data={turnos} />
}
