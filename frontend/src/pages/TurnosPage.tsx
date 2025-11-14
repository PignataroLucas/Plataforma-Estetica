import React, { useEffect, useState } from 'react'
import { Card, Button, Input, Modal, ModalHeader, ModalBody, ModalFooter } from '../components/ui'
import { TurnosList } from '../components/turnos/TurnosList'
import { TurnoForm } from '../components/turnos/TurnoForm'
import { useTurnos } from '../hooks/useTurnos'
import type { TurnoList, Turno } from '../types/models'

export default function TurnosPage() {
  const {
    turnos,
    loading,
    error,
    fetchTurnos,
    createTurno,
    updateTurno,
    deleteTurno,
  } = useTurnos()

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
  const [selectedTurno, setSelectedTurno] = useState<TurnoList | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterEstado, setFilterEstado] = useState('')
  const [filterFecha, setFilterFecha] = useState('')

  useEffect(() => {
    loadTurnos()
  }, [filterEstado, filterFecha])

  const loadTurnos = () => {
    const params: any = {}
    if (filterEstado) params.estado = filterEstado
    if (filterFecha) params.fecha_desde = filterFecha
    fetchTurnos(params)
  }

  const handleCreateTurno = async (data: Partial<Turno>) => {
    try {
      await createTurno(data)
      setIsCreateModalOpen(false)
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
    }
  }

  const openEditModal = (turno: TurnoList) => {
    setSelectedTurno(turno)
    setIsEditModalOpen(true)
  }

  const openDeleteModal = (turno: TurnoList) => {
    setSelectedTurno(turno)
    setIsDeleteModalOpen(true)
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
        <Button variant="primary" onClick={() => setIsCreateModalOpen(true)}>
          + Nuevo Turno
        </Button>
      </div>

      <Card>
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

            <Input
              type="date"
              placeholder="Filtrar por fecha"
              value={filterFecha}
              onChange={(e) => setFilterFecha(e.target.value)}
            />
          </div>
        </div>

        <div className="p-6">
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 text-red-700 rounded-md">
              {error}
            </div>
          )}

          <TurnosList
            turnos={filteredTurnos}
            onEdit={openEditModal}
            onDelete={openDeleteModal}
            loading={loading}
          />
        </div>
      </Card>

      {/* Modal de Crear */}
      <Modal isOpen={isCreateModalOpen} onClose={() => setIsCreateModalOpen(false)} size="large">
        <ModalHeader>Nuevo Turno</ModalHeader>
        <ModalBody>
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
      <Modal isOpen={isEditModalOpen} onClose={() => setIsEditModalOpen(false)} size="large">
        <ModalHeader>Editar Turno</ModalHeader>
        <ModalBody>
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
