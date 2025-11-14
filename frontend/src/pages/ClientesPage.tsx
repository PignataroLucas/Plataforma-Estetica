import { useState, useEffect } from 'react'
import { useClientes } from '@/hooks/useClientes'
import { Cliente } from '@/types/models'
import {
  Button,
  Input,
  Modal,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Card,
  CardHeader,
  CardBody,
} from '@/components/ui'
import ClientesList from '@/components/clientes/ClientesList'
import ClienteForm from '@/components/clientes/ClienteForm'

/**
 * ClientesPage - Container Component (Patrón Container/Presenter)
 * Aplica principios SOLID:
 * - SRP: Coordina la gestión de clientes (no renderiza UI compleja)
 * - DIP: Depende de abstracciones (useClientes hook)
 * - OCP: Extensible via componentes composables
 *
 * Responsabilidades:
 * 1. Coordinar estado de la página (modals, búsqueda, etc.)
 * 2. Delegar lógica de negocio al hook useClientes
 * 3. Delegar presentación a ClientesList y ClienteForm
 */
export default function ClientesPage() {
  const {
    clientes,
    loading,
    fetchClientes,
    createCliente,
    updateCliente,
    deleteCliente,
    searchClientes,
  } = useClientes()

  // Estado del modal
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [modalMode, setModalMode] = useState<'create' | 'edit' | 'view'>('create')
  const [selectedCliente, setSelectedCliente] = useState<Cliente | null>(null)

  // Estado de búsqueda
  const [searchQuery, setSearchQuery] = useState('')

  // Estado del modal de confirmación de eliminación
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
  const [clienteToDelete, setClienteToDelete] = useState<Cliente | null>(null)

  // Cargar clientes al montar el componente
  useEffect(() => {
    fetchClientes()
  }, [fetchClientes])

  /**
   * Handlers del modal (SRP - responsabilidad única)
   */
  const handleOpenCreateModal = () => {
    setModalMode('create')
    setSelectedCliente(null)
    setIsModalOpen(true)
  }

  const handleOpenEditModal = (cliente: Cliente) => {
    setModalMode('edit')
    setSelectedCliente(cliente)
    setIsModalOpen(true)
  }

  const handleOpenViewModal = (cliente: Cliente) => {
    setModalMode('view')
    setSelectedCliente(cliente)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setSelectedCliente(null)
  }

  /**
   * Handler de submit del formulario (SRP)
   */
  const handleFormSubmit = async (data: Partial<Cliente>) => {
    try {
      if (modalMode === 'edit' && selectedCliente) {
        await updateCliente(selectedCliente.id, data)
      } else {
        await createCliente(data)
      }
      handleCloseModal()
    } catch (error) {
      // El error ya se maneja en el hook con toast
      console.error('Error al guardar cliente:', error)
    }
  }

  /**
   * Handler de eliminación (SRP)
   */
  const handleOpenDeleteModal = (cliente: Cliente) => {
    setClienteToDelete(cliente)
    setIsDeleteModalOpen(true)
  }

  const handleCloseDeleteModal = () => {
    setIsDeleteModalOpen(false)
    setClienteToDelete(null)
  }

  const handleConfirmDelete = async () => {
    if (clienteToDelete) {
      try {
        await deleteCliente(clienteToDelete.id)
        handleCloseDeleteModal()
      } catch (error) {
        console.error('Error al eliminar cliente:', error)
      }
    }
  }

  /**
   * Handler de búsqueda (SRP)
   */
  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      await searchClientes(searchQuery)
    } else {
      await fetchClientes()
    }
  }

  const handleClearSearch = () => {
    setSearchQuery('')
    fetchClientes()
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Gestión de Clientes
        </h1>
        <p className="text-gray-600">
          Administra la información de tus clientes
        </p>
      </div>

      {/* Toolbar */}
      <Card className="mb-6">
        <CardBody>
          <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
            {/* Búsqueda */}
            <form onSubmit={handleSearch} className="flex-1 w-full md:max-w-md">
              <div className="flex gap-2">
                <Input
                  placeholder="Buscar por nombre, email o teléfono..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  fullWidth
                />
                <Button type="submit" variant="secondary">
                  Buscar
                </Button>
                {searchQuery && (
                  <Button type="button" variant="ghost" onClick={handleClearSearch}>
                    Limpiar
                  </Button>
                )}
              </div>
            </form>

            {/* Botón Crear */}
            <Button
              variant="primary"
              onClick={handleOpenCreateModal}
              leftIcon={
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              }
            >
              Nuevo Cliente
            </Button>
          </div>
        </CardBody>
      </Card>

      {/* Lista de Clientes */}
      <Card>
        <ClientesList
          clientes={clientes}
          loading={loading}
          onEdit={handleOpenEditModal}
          onDelete={handleOpenDeleteModal}
          onView={handleOpenViewModal}
        />
      </Card>

      {/* Modal Create/Edit */}
      <Modal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        size="md"
        showCloseButton={true}
      >
        <ModalHeader>
          <h2 className="text-xl font-bold text-gray-900">
            {modalMode === 'create' && 'Nuevo Cliente'}
            {modalMode === 'edit' && 'Editar Cliente'}
            {modalMode === 'view' && 'Detalles del Cliente'}
          </h2>
        </ModalHeader>
        <ModalBody>
          {modalMode === 'view' && selectedCliente ? (
            // Vista de solo lectura
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold mb-2">Datos Personales</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-gray-700">Nombre:</span>
                    <p>{selectedCliente.nombre} {selectedCliente.apellido}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Email:</span>
                    <p>{selectedCliente.email}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Teléfono:</span>
                    <p>{selectedCliente.telefono}</p>
                  </div>
                  {selectedCliente.fecha_nacimiento && (
                    <div>
                      <span className="font-medium text-gray-700">Fecha de Nacimiento:</span>
                      <p>{new Date(selectedCliente.fecha_nacimiento).toLocaleDateString('es-AR')}</p>
                    </div>
                  )}
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold mb-2">Dirección</h3>
                <p className="text-sm">{selectedCliente.direccion}</p>
                <p className="text-sm">{selectedCliente.ciudad}, {selectedCliente.provincia} - {selectedCliente.codigo_postal}</p>
              </div>

              {(selectedCliente.alergias || selectedCliente.contraindicaciones) && (
                <div>
                  <h3 className="text-lg font-semibold mb-2">Información Médica</h3>
                  {selectedCliente.alergias && (
                    <div className="mb-2">
                      <span className="font-medium text-gray-700 text-sm">Alergias:</span>
                      <p className="text-sm">{selectedCliente.alergias}</p>
                    </div>
                  )}
                  {selectedCliente.contraindicaciones && (
                    <div>
                      <span className="font-medium text-gray-700 text-sm">Contraindicaciones:</span>
                      <p className="text-sm">{selectedCliente.contraindicaciones}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            // Formulario de creación/edición
            <ClienteForm
              cliente={selectedCliente}
              onSubmit={handleFormSubmit}
              onCancel={handleCloseModal}
              loading={loading}
              formId="cliente-form"
              showButtons={false}
            />
          )}
        </ModalBody>
        {modalMode === 'view' ? (
          <ModalFooter>
            <Button variant="secondary" onClick={handleCloseModal}>
              Cerrar
            </Button>
            <Button variant="primary" onClick={() => setModalMode('edit')}>
              Editar
            </Button>
          </ModalFooter>
        ) : (
          <ModalFooter>
            <Button
              type="button"
              variant="secondary"
              onClick={handleCloseModal}
              disabled={loading}
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              form="cliente-form"
              variant="primary"
              loading={loading}
            >
              {modalMode === 'edit' ? 'Actualizar Cliente' : 'Crear Cliente'}
            </Button>
          </ModalFooter>
        )}
      </Modal>

      {/* Modal de Confirmación de Eliminación */}
      <Modal
        isOpen={isDeleteModalOpen}
        onClose={handleCloseDeleteModal}
        size="sm"
      >
        <ModalHeader>
          <h2 className="text-xl font-bold text-gray-900">
            Confirmar Eliminación
          </h2>
        </ModalHeader>
        <ModalBody>
          <p className="text-gray-700">
            ¿Estás seguro que deseas eliminar al cliente{' '}
            <strong>{clienteToDelete?.nombre} {clienteToDelete?.apellido}</strong>?
          </p>
          <p className="text-sm text-red-600 mt-2">
            Esta acción no se puede deshacer.
          </p>
        </ModalBody>
        <ModalFooter>
          <Button variant="secondary" onClick={handleCloseDeleteModal}>
            Cancelar
          </Button>
          <Button variant="danger" onClick={handleConfirmDelete} loading={loading}>
            Eliminar
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  )
}
