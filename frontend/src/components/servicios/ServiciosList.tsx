import { Servicio } from '@/types/models'
import { Table, Column, Badge, Button } from '@/components/ui'

/**
 * ServiciosList - Lista de Servicios (Presentación)
 * Aplica principios SOLID:
 * - SRP: Solo renderiza la lista de servicios
 * - DIP: Recibe datos y callbacks como props
 * - OCP: Extensible via props y column configuration
 */

interface ServiciosListProps {
  servicios: Servicio[]
  loading?: boolean
  onEdit: (servicio: Servicio) => void
  onDelete: (servicio: Servicio) => void
}

export default function ServiciosList({
  servicios,
  loading = false,
  onEdit,
  onDelete,
}: ServiciosListProps) {
  /**
   * Formato de precio en pesos argentinos
   */
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS',
      minimumFractionDigits: 0,
    }).format(price)
  }

  /**
   * Formato de duración en formato legible
   */
  const formatDuration = (minutes: number) => {
    if (minutes < 60) {
      return `${minutes} min`
    }
    const hours = Math.floor(minutes / 60)
    const remainingMinutes = minutes % 60
    if (remainingMinutes === 0) {
      return `${hours}h`
    }
    return `${hours}h ${remainingMinutes}min`
  }

  /**
   * Definición de columnas (OCP - extensible sin modificar componente)
   */
  const columns: Column<Servicio>[] = [
    {
      key: 'nombre',
      header: 'Servicio',
      width: '40%',
    },
    {
      key: 'duracion_minutos',
      header: 'Duración',
      width: '20%',
      accessor: (row) => formatDuration(row.duracion_minutos),
    },
    {
      key: 'precio',
      header: 'Precio',
      width: '20%',
      accessor: (row) => (
        <span className="font-semibold text-green-600">
          {formatPrice(row.precio)}
        </span>
      ),
    },
    {
      key: 'activo',
      header: 'Estado',
      width: '10%',
      align: 'center',
      accessor: (row) => (
        <Badge variant={row.activo ? 'success' : 'gray'} dot>
          {row.activo ? 'Activo' : 'Inactivo'}
        </Badge>
      ),
    },
    {
      key: 'acciones',
      header: 'Acciones',
      width: '10%',
      align: 'right',
      accessor: (row) => (
        <div className="flex gap-2 justify-end">
          <button
            onClick={(e) => {
              e.stopPropagation()
              onEdit(row)
            }}
            className="text-primary-600 hover:text-primary-800 transition-colors"
            title="Editar"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation()
              onDelete(row)
            }}
            className="text-red-600 hover:text-red-800 transition-colors"
            title="Eliminar"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      ),
    },
  ]

  return (
    <Table
      data={servicios}
      columns={columns}
      loading={loading}
      emptyMessage="No se encontraron servicios. Crea uno para comenzar."
      hoverable
      striped
    />
  )
}
