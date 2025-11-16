import { useEffect, useState } from 'react'
import { Card, Button, Input, Modal, ModalHeader, ModalBody, ModalFooter } from '../components/ui'
import { TurnosList } from '../components/turnos/TurnosList'
import { CalendarView } from '../components/turnos/CalendarView'
import { TurnoForm } from '../components/turnos/TurnoForm'
import { useTurnos } from '../hooks/useTurnos'
import type { TurnoList, Turno } from '../types/models'

type TabType = 'hoy' | 'proximos' | 'historial'
type ViewType = 'list' | 'calendar'

export default function TurnosPage() {
  const {
    turnos,
    loading,
    error,
    fetchTurnos,
    createTurno,
    updateTurno,
    deleteTurno,
    cambiarEstado,
    clearError,
  } = useTurnos()

  const [activeTab, setActiveTab] = useState<TabType>('hoy')
  const [viewType, setViewType] = useState<ViewType>('list')
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
  const [selectedTurno, setSelectedTurno] = useState<TurnoList | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterEstado, setFilterEstado] = useState('')
  const [filterProfesional, setFilterProfesional] = useState('')

  useEffect(() => {
    loadTurnos()
  }, [activeTab, filterEstado, filterProfesional, viewType])

  const getDateFilters = () => {
    const now = new Date()
    const todayStr = now.toISOString().split('T')[0]
    const nowISO = now.toISOString()

    // Si estamos en vista calendario, cargar un rango amplio
    if (viewType === 'calendar') {
      const ago7Days = new Date(now)
      ago7Days.setDate(now.getDate() - 7)
      ago7Days.setHours(0, 0, 0, 0)

      const in30Days = new Date(now)
      in30Days.setDate(now.getDate() + 30)
      in30Days.setHours(23, 59, 59)

      return {
        fecha_desde: ago7Days.toISOString(),
        fecha_hasta: in30Days.toISOString(),
      }
    }

    // Si estamos en vista lista, aplicar filtros por tab
    switch (activeTab) {
      case 'hoy':
        // Solo turnos de hoy que NO han pasado (desde ahora hasta fin del día)
        const endOfToday = `${todayStr}T23:59:59`
        return {
          fecha_desde: nowISO,
          fecha_hasta: endOfToday,
        }
      case 'proximos':
        // Turnos desde mañana hasta 7 días en el futuro
        const tomorrow = new Date(now)
        tomorrow.setDate(now.getDate() + 1)
        tomorrow.setHours(0, 0, 0, 0)
        const in7Days = new Date(tomorrow)
        in7Days.setDate(tomorrow.getDate() + 7)
        return {
          fecha_desde: tomorrow.toISOString(),
          fecha_hasta: in7Days.toISOString(),
        }
      case 'historial':
        // Turnos que ya pasaron (últimos 30 días hasta ahora)
        const ago30Days = new Date(now)
        ago30Days.setDate(now.getDate() - 30)
        return {
          fecha_desde: ago30Days.toISOString(),
          fecha_hasta: nowISO,
        }
      default:
        return {}
    }
  }

  const loadTurnos = () => {
    const params: any = { ...getDateFilters() }

    // Solo aplicar filtros de estado y profesional en vista lista
    if (viewType === 'list') {
      if (filterEstado) params.estado = filterEstado
      if (filterProfesional) params.profesional = filterProfesional
    }

    fetchTurnos(params)
  }

  const handleCreateTurno = async (data: Partial<Turno>) => {
    try {
      await createTurno(data)
      setIsCreateModalOpen(false)
      loadTurnos() // Recargar con filtros actuales
    } catch (err) {
      console.error('Error creating turno:', err)
    }
  }

  const handleEditTurno = async (data: Partial<Turno>) => {
    if (!selectedTurno) return

    try {
      await updateTurno(selectedTurno.id, data)
      setIsEditModalOpen(false)
      setSelectedTurno(null)
      loadTurnos() // Recargar con filtros actuales
    } catch (err) {
      console.error('Error updating turno:', err)
    }
  }

  const handleDeleteTurno = async () => {
    if (!selectedTurno) return

    const success = await deleteTurno(selectedTurno.id)
    if (success) {
      setIsDeleteModalOpen(false)
      setSelectedTurno(null)
      loadTurnos() // Recargar con filtros actuales
    }
  }

  const handleQuickAction = async (turnoId: number, newEstado: string) => {
    const estadoLabels: Record<string, string> = {
      COMPLETADO: 'completado',
      CANCELADO: 'cancelado',
      NO_SHOW: 'No Show',
    }

    const confirm = window.confirm(
      `¿Confirmas que deseas marcar este turno como ${estadoLabels[newEstado]}?`
    )

    if (!confirm) return

    const success = await cambiarEstado(turnoId, newEstado)
    if (success) {
      loadTurnos() // Recargar para reflejar el cambio
    }
  }

  const openEditModal = (turno: TurnoList) => {
    clearError()
    setSelectedTurno(turno)
    setIsEditModalOpen(true)
  }

  const openDeleteModal = (turno: TurnoList) => {
    setSelectedTurno(turno)
    setIsDeleteModalOpen(true)
  }

  // Handlers para el calendario
  const handleCalendarSelectEvent = (turno: TurnoList) => {
    openEditModal(turno)
  }

  const handleCalendarSelectSlot = (_slotInfo: { start: Date; end: Date }) => {
    // Pre-llenar el modal de creación con la fecha/hora seleccionada
    clearError()
    setIsCreateModalOpen(true)
    // TODO: Pre-llenar fecha y hora en el formulario usando slotInfo
  }

  const filteredTurnos = turnos.filter(turno => {
    if (!searchTerm) return true
    const search = searchTerm.toLowerCase()
    return (
      turno.cliente_nombre?.toLowerCase().includes(search) ||
      turno.servicio_nombre?.toLowerCase().includes(search) ||
      turno.profesional_nombre?.toLowerCase().includes(search)
    )
  })

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Turnos</h1>
          <p className="text-gray-600 mt-1">Gestiona las citas y reservas</p>
        </div>
        <div className="flex gap-2">
          {/* Toggle de vistas */}
          <div className="flex bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setViewType('list')}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                viewType === 'list'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              📋 Lista
            </button>
            <button
              onClick={() => setViewType('calendar')}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                viewType === 'calendar'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              📅 Calendario
            </button>
          </div>
          <Button variant="primary" onClick={() => {
            clearError()
            setIsCreateModalOpen(true)
          }}>
            + Nuevo Turno
          </Button>
        </div>
      </div>

      {/* Tabs - Solo mostrar en vista de lista */}
      {viewType === 'list' && (
        <div className="flex space-x-1 border-b border-gray-200 bg-white rounded-t-lg px-4">
        <button
          onClick={() => setActiveTab('hoy')}
          className={`px-6 py-3 text-sm font-medium transition-colors border-b-2 ${
            activeTab === 'hoy'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          }`}
        >
          📅 Hoy
        </button>
        <button
          onClick={() => setActiveTab('proximos')}
          className={`px-6 py-3 text-sm font-medium transition-colors border-b-2 ${
            activeTab === 'proximos'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          }`}
        >
          🔜 Próximos
        </button>
        <button
          onClick={() => setActiveTab('historial')}
          className={`px-6 py-3 text-sm font-medium transition-colors border-b-2 ${
            activeTab === 'historial'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          }`}
        >
          📊 Historial
        </button>
        </div>
      )}

      <Card className={viewType === 'list' ? 'rounded-t-none' : ''}>
        {/* Filtros - Solo en vista lista */}
        {viewType === 'list' && (
          <div className="p-4 border-b border-gray-200">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Input
                type="search"
                placeholder="Buscar por cliente, servicio o profesional..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />

              <select
                value={filterEstado}
                onChange={(e) => setFilterEstado(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Todos los estados</option>
                <option value="PENDIENTE">Pendiente</option>
                <option value="CONFIRMADO">Confirmado</option>
                <option value="COMPLETADO">Completado</option>
                <option value="CANCELADO">Cancelado</option>
                <option value="NO_SHOW">No Show</option>
              </select>

              <select
                value={filterProfesional}
                onChange={(e) => setFilterProfesional(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Todos los profesionales</option>
                {/* TODO: Cargar lista de profesionales dinámicamente */}
              </select>
            </div>
          </div>
        )}

        {/* Contenido según vista seleccionada */}
        {viewType === 'list' ? (
          <div className="p-6">
            <TurnosList
              turnos={filteredTurnos}
              onEdit={openEditModal}
              onDelete={openDeleteModal}
              onQuickAction={handleQuickAction}
              loading={loading}
            />
          </div>
        ) : (
          <div className="p-6">
            <CalendarView
              turnos={turnos}
              onSelectEvent={handleCalendarSelectEvent}
              onSelectSlot={handleCalendarSelectSlot}
              loading={loading}
            />
          </div>
        )}
      </Card>

      {/* Modal de Crear */}
      <Modal isOpen={isCreateModalOpen} onClose={() => setIsCreateModalOpen(false)} size="lg">
        <ModalHeader>Nuevo Turno</ModalHeader>
        <ModalBody>
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 text-red-700 rounded-md">
              {error}
            </div>
          )}
          <TurnoForm
            formId="create-turno-form"
            onSubmit={handleCreateTurno}
            onCancel={() => setIsCreateModalOpen(false)}
          />
        </ModalBody>
        <ModalFooter>
          <Button variant="secondary" onClick={() => setIsCreateModalOpen(false)}>
            Cancelar
          </Button>
          <Button type="submit" form="create-turno-form" variant="primary">
            Crear Turno
          </Button>
        </ModalFooter>
      </Modal>

      {/* Modal de Editar */}
      <Modal isOpen={isEditModalOpen} onClose={() => setIsEditModalOpen(false)} size="lg">
        <ModalHeader>Editar Turno</ModalHeader>
        <ModalBody>
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 text-red-700 rounded-md">
              {error}
            </div>
          )}
          {selectedTurno && (
            <TurnoForm
              formId="edit-turno-form"
              initialData={selectedTurno}
              onSubmit={handleEditTurno}
              onCancel={() => setIsEditModalOpen(false)}
              submitLabel="Actualizar"
            />
          )}
        </ModalBody>
        <ModalFooter>
          <Button variant="secondary" onClick={() => setIsEditModalOpen(false)}>
            Cancelar
          </Button>
          <Button type="submit" form="edit-turno-form" variant="primary">
            Actualizar
          </Button>
        </ModalFooter>
      </Modal>

      {/* Modal de Eliminar */}
      <Modal isOpen={isDeleteModalOpen} onClose={() => setIsDeleteModalOpen(false)}>
        <ModalHeader>Eliminar Turno</ModalHeader>
        <ModalBody>
          {selectedTurno && (
            <p>
              ¿Estás seguro de que deseas eliminar el turno de{' '}
              <strong>{selectedTurno.cliente_nombre}</strong> para{' '}
              <strong>{selectedTurno.servicio_nombre}</strong>?
            </p>
          )}
        </ModalBody>
        <ModalFooter>
          <Button variant="secondary" onClick={() => setIsDeleteModalOpen(false)}>
            Cancelar
          </Button>
          <Button variant="danger" onClick={handleDeleteTurno}>
            Eliminar
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  )
}
