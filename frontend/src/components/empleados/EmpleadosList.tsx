import React from 'react'
import { Table, Badge, Button } from '../ui'
import type { Usuario } from '../../types/models'

interface EmpleadosListProps {
  empleados: Usuario[]
  onEdit: (empleado: Usuario) => void
  onDelete: (empleado: Usuario) => void
  onToggleStatus?: (empleado: Usuario) => void
  loading?: boolean
}

const getRolBadgeVariant = (rol: string): 'success' | 'warning' | 'error' | 'info' | 'default' => {
  switch (rol) {
    case 'ADMIN':
      return 'error'
    case 'MANAGER':
      return 'warning'
    case 'EMPLEADO':
      return 'info'
    default:
      return 'default'
  }
}

const getRolLabel = (rol: string) => {
  const labels: Record<string, string> = {
    ADMIN: 'Administrador',
    MANAGER: 'Manager',
    EMPLEADO: 'Empleado',
  }
  return labels[rol] || rol
}

const formatDate = (dateString?: string) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

export const EmpleadosList: React.FC<EmpleadosListProps> = ({
  empleados,
  onEdit,
  onDelete,
  onToggleStatus,
  loading
}) => {
  const columns = [
    {
      key: 'nombre_completo',
      header: 'Nombre',
      accessor: (empleado: Usuario) => {
        const nombreCompleto = `${empleado.first_name} ${empleado.last_name}`.trim() || empleado.username
        return (
          <div className="flex flex-col">
            <span className="font-medium">{nombreCompleto}</span>
            <span className="text-sm text-gray-600">{empleado.username}</span>
          </div>
        )
      },
    },
    {
      key: 'email',
      header: 'Email',
    },
    {
      key: 'telefono',
      header: 'Teléfono',
      accessor: (empleado: Usuario) => empleado.telefono || <span className="text-gray-400">-</span>,
    },
    {
      key: 'rol',
      header: 'Rol',
      accessor: (empleado: Usuario) => (
        <Badge variant={getRolBadgeVariant(empleado.rol)}>
          {getRolLabel(empleado.rol)}
        </Badge>
      ),
    },
    {
      key: 'especialidades',
      header: 'Especialidades',
      accessor: (empleado: Usuario) => {
        if (!empleado.especialidades) return <span className="text-gray-400 italic">Sin especificar</span>
        const especialidadesText = empleado.especialidades.length > 50
          ? `${empleado.especialidades.substring(0, 50)}...`
          : empleado.especialidades
        return <span className="text-sm">{especialidadesText}</span>
      },
    },
    {
      key: 'fecha_ingreso',
      header: 'Fecha Ingreso',
      accessor: (empleado: Usuario) => formatDate(empleado.fecha_ingreso),
    },
    {
      key: 'activo',
      header: 'Estado',
      accessor: (empleado: Usuario) => (
        <Badge variant={empleado.activo ? 'success' : 'error'}>
          {empleado.activo ? 'Activo' : 'Inactivo'}
        </Badge>
      ),
    },
    {
      key: 'acciones',
      header: 'Acciones',
      accessor: (empleado: Usuario) => (
        <div className="flex gap-2">
          {onToggleStatus && (
            <Button
              variant={empleado.activo ? 'secondary' : 'success'}
              size="small"
              onClick={() => onToggleStatus(empleado)}
            >
              {empleado.activo ? 'Desactivar' : 'Activar'}
            </Button>
          )}
          <Button
            variant="secondary"
            size="small"
            onClick={() => onEdit(empleado)}
          >
            Editar
          </Button>
          <Button
            variant="danger"
            size="small"
            onClick={() => onDelete(empleado)}
          >
            Eliminar
          </Button>
        </div>
      ),
    },
  ]

  if (loading) {
    return <div className="text-center py-8">Cargando empleados...</div>
  }

  if (empleados.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No hay empleados registrados. Crea el primero usando el botón "Nuevo Empleado".
      </div>
    )
  }

  return <Table columns={columns} data={empleados} />
}
