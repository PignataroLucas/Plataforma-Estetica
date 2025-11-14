import React, { useEffect, useState } from 'react'
import { Card, Button, Input, Modal, ModalHeader, ModalBody, ModalFooter } from '../components/ui'
import { EmpleadosList } from '../components/empleados/EmpleadosList'
import { EmpleadoForm } from '../components/empleados/EmpleadoForm'
import { useEmpleados } from '../hooks/useEmpleados'
import type { Usuario } from '../types/models'

export default function EmpleadosPage() {
  const {
    empleados,
    loading,
    error,
    fetchEmpleados,
    createEmpleado,
    updateEmpleado,
    deleteEmpleado,
    cambiarEstado,
  } = useEmpleados()

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
  const [selectedEmpleado, setSelectedEmpleado] = useState<Usuario | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterRol, setFilterRol] = useState('')
  const [filterActivo, setFilterActivo] = useState('')

  useEffect(() => {
    loadEmpleados()
  }, [filterRol, filterActivo])

  const loadEmpleados = () => {
    const params: any = {}
    if (filterRol) params.rol = filterRol
    if (filterActivo !== '') params.activo = filterActivo === 'true'
    fetchEmpleados(params)
  }

  const handleCreateEmpleado = async (data: any) => {
    try {
      await createEmpleado(data)
      setIsCreateModalOpen(false)
    } catch (err) {
      console.error('Error creating empleado:', err)
    }
  }

  const handleEditEmpleado = async (data: Partial<Usuario>) => {
    if (!selectedEmpleado) return

    try {
      await updateEmpleado(selectedEmpleado.id, data)
      setIsEditModalOpen(false)
      setSelectedEmpleado(null)
    } catch (err) {
      console.error('Error updating empleado:', err)
    }
  }

  const handleDeleteEmpleado = async () => {
    if (!selectedEmpleado) return

    const success = await deleteEmpleado(selectedEmpleado.id)
    if (success) {
      setIsDeleteModalOpen(false)
      setSelectedEmpleado(null)
    }
  }

  const handleToggleStatus = async (empleado: Usuario) => {
    await cambiarEstado(empleado.id, !empleado.activo)
  }

  const openEditModal = (empleado: Usuario) => {
    setSelectedEmpleado(empleado)
    setIsEditModalOpen(true)
  }

  const openDeleteModal = (empleado: Usuario) => {
    setSelectedEmpleado(empleado)
    setIsDeleteModalOpen(true)
  }

  const filteredEmpleados = empleados.filter(empleado => {
    if (!searchTerm) return true
    const search = searchTerm.toLowerCase()
    const nombreCompleto = `${empleado.first_name} ${empleado.last_name}`.toLowerCase()
    return (
      nombreCompleto.includes(search) ||
      empleado.username.toLowerCase().includes(search) ||
      empleado.email?.toLowerCase().includes(search) ||
      empleado.especialidades?.toLowerCase().includes(search)
    )
  })

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Empleados</h1>
          <p className="text-gray-600 mt-1">Gestiona el equipo de profesionales</p>
        </div>
        <Button variant="primary" onClick={() => setIsCreateModalOpen(true)}>
          + Nuevo Empleado
        </Button>
      </div>

      <Card>
        <div className="p-4 border-b border-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Input
              type="search"
              placeholder="Buscar por nombre, email o especialidad..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />

            <select
              value={filterRol}
              onChange={(e) => setFilterRol(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todos los roles</option>
              <option value="ADMIN">Administrador</option>
              <option value="MANAGER">Manager</option>
              <option value="EMPLEADO">Empleado</option>
            </select>

            <select
              value={filterActivo}
              onChange={(e) => setFilterActivo(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todos los estados</option>
              <option value="true">Activos</option>
              <option value="false">Inactivos</option>
            </select>
          </div>
        </div>

        <div className="p-6">
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 text-red-700 rounded-md">
              {error}
            </div>
          )}

          <EmpleadosList
            empleados={filteredEmpleados}
            onEdit={openEditModal}
            onDelete={openDeleteModal}
            onToggleStatus={handleToggleStatus}
            loading={loading}
          />
        </div>
      </Card>

      {/* Modal de Crear */}
      <Modal isOpen={isCreateModalOpen} onClose={() => setIsCreateModalOpen(false)} size="large">
        <ModalHeader>Nuevo Empleado</ModalHeader>
        <ModalBody>
          <EmpleadoForm
            formId="create-empleado-form"
            onSubmit={handleCreateEmpleado}
            onCancel={() => setIsCreateModalOpen(false)}
            isEditing={false}
          />
        </ModalBody>
        <ModalFooter>
          <Button variant="secondary" onClick={() => setIsCreateModalOpen(false)}>
            Cancelar
          </Button>
          <Button type="submit" form="create-empleado-form" variant="primary">
            Crear Empleado
          </Button>
        </ModalFooter>
      </Modal>

      {/* Modal de Editar */}
      <Modal isOpen={isEditModalOpen} onClose={() => setIsEditModalOpen(false)} size="large">
        <ModalHeader>Editar Empleado</ModalHeader>
        <ModalBody>
          {selectedEmpleado && (
            <EmpleadoForm
              formId="edit-empleado-form"
              initialData={selectedEmpleado}
              onSubmit={handleEditEmpleado}
              onCancel={() => setIsEditModalOpen(false)}
              submitLabel="Actualizar"
              isEditing={true}
            />
          )}
        </ModalBody>
        <ModalFooter>
          <Button variant="secondary" onClick={() => setIsEditModalOpen(false)}>
            Cancelar
          </Button>
          <Button type="submit" form="edit-empleado-form" variant="primary">
            Actualizar
          </Button>
        </ModalFooter>
      </Modal>

      {/* Modal de Eliminar */}
      <Modal isOpen={isDeleteModalOpen} onClose={() => setIsDeleteModalOpen(false)}>
        <ModalHeader>Eliminar Empleado</ModalHeader>
        <ModalBody>
          {selectedEmpleado && (
            <p>
              ¿Estás seguro de que deseas eliminar a{' '}
              <strong>{selectedEmpleado.first_name} {selectedEmpleado.last_name}</strong>?
              <br />
              <span className="text-sm text-gray-600">
                Esta acción no se puede deshacer.
              </span>
            </p>
          )}
        </ModalBody>
        <ModalFooter>
          <Button variant="secondary" onClick={() => setIsDeleteModalOpen(false)}>
            Cancelar
          </Button>
          <Button variant="danger" onClick={handleDeleteEmpleado}>
            Eliminar
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  )
}
