import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
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
  CardBody,
} from '@/components/ui'
import ClientesList from '@/components/clientes/ClientesList'
import ClienteForm from '@/components/clientes/ClienteForm'
import DuplicadosModal from '@/components/clientes/DuplicadosModal'
import SegmentosAppModal from '@/components/clientes/SegmentosAppModal'
import { useAuthStore } from '@/stores/authStore'

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
  const navigate = useNavigate()
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
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create')
  const [selectedCliente, setSelectedCliente] = useState<Cliente | null>(null)

  // Estado de búsqueda
  const [searchQuery, setSearchQuery] = useState('')

  // Estado del modal de confirmación de eliminación
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
  const [clienteToDelete, setClienteToDelete] = useState<Cliente | null>(null)

  // Estado del modal de duplicados
  const [isDuplicadosOpen, setIsDuplicadosOpen] = useState(false)

  // Segmentos de la app: solo admin, porque el porcentaje es margen del centro
  // y define lo que la app le cobra a cada clienta.
  const [isSegmentosOpen, setIsSegmentosOpen] = useState(false)
  const esAdmin = useAuthStore((s) => s.user?.rol === 'ADMIN')

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
    navigate(`/clientes/${cliente.id}`)
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

            {/* Acciones */}
            <div className="flex gap-2">
              <Button
                variant="secondary"
                onClick={() => setIsDuplicadosOpen(true)}
                leftIcon={
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                  </svg>
                }
              >
                Duplicados
              </Button>
              {esAdmin && (
                <Button
                  variant="secondary"
                  onClick={() => setIsSegmentosOpen(true)}
                  leftIcon={
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5a1.99 1.99 0 011.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.99 1.99 0 013 12V7a4 4 0 014-4z" />
                    </svg>
                  }
                >
                  Segmentos de la app
                </Button>
              )}
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
          </h2>
        </ModalHeader>
        <ModalBody>
          <ClienteForm
            cliente={selectedCliente}
            onSubmit={handleFormSubmit}
            onCancel={handleCloseModal}
            loading={loading}
            formId="cliente-form"
            showButtons={false}
          />
        </ModalBody>
        <ModalFooter>
          <Button type="button" variant="secondary" onClick={handleCloseModal}>
            Cancelar
          </Button>
          <Button type="submit" form="cliente-form" variant="primary" loading={loading}>
            {modalMode === 'create' ? 'Crear Cliente' : 'Actualizar Cliente'}
          </Button>
        </ModalFooter>
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

      {/* Modal de Duplicados */}
      <DuplicadosModal
        isOpen={isDuplicadosOpen}
        onClose={() => setIsDuplicadosOpen(false)}
        onMerged={fetchClientes}
      />

      {/* Segmentos de la app */}
      <SegmentosAppModal
        isOpen={isSegmentosOpen}
        onClose={() => setIsSegmentosOpen(false)}
        onCambios={fetchClientes}
      />
    </div>
  )
}
