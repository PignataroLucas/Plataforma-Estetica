import { useState, useEffect } from 'react'
import { useServicios } from '@/hooks/useServicios'
import { Servicio } from '@/types/models'
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
import ServiciosList from '@/components/servicios/ServiciosList'
import ServicioForm from '@/components/servicios/ServicioForm'

/**
 * ServiciosPage - Container Component (Patrón Container/Presenter)
 * Aplica principios SOLID:
 * - SRP: Coordina la gestión de servicios (no renderiza UI compleja)
 * - DIP: Depende de abstracciones (useServicios hook)
 * - OCP: Extensible via componentes composables
 */
export default function ServiciosPage() {
  const {
    servicios,
    loading,
    fetchServicios,
    createServicio,
    updateServicio,
    deleteServicio,
    searchServicios,
  } = useServicios()

  // Estado del modal
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create')
  const [selectedServicio, setSelectedServicio] = useState<Servicio | null>(null)

  // Estado de búsqueda
  const [searchQuery, setSearchQuery] = useState('')

  // Estado del modal de confirmación de eliminación
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
  const [servicioToDelete, setServicioToDelete] = useState<Servicio | null>(null)

  // Cargar servicios al montar el componente
  useEffect(() => {
    fetchServicios()
  }, [fetchServicios])

  /**
   * Handlers del modal (SRP - responsabilidad única)
   */
  const handleOpenCreateModal = () => {
    setModalMode('create')
    setSelectedServicio(null)
    setIsModalOpen(true)
  }

  const handleOpenEditModal = (servicio: Servicio) => {
    setModalMode('edit')
    setSelectedServicio(servicio)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setSelectedServicio(null)
  }

  /**
   * Handler de submit del formulario (SRP)
   */
  const handleFormSubmit = async (data: Partial<Servicio>) => {
    try {
      if (modalMode === 'edit' && selectedServicio) {
        await updateServicio(selectedServicio.id, data)
      } else {
        await createServicio(data)
      }
      handleCloseModal()
    } catch (error) {
      console.error('Error al guardar servicio:', error)
    }
  }

  /**
   * Handler de eliminación (SRP)
   */
  const handleOpenDeleteModal = (servicio: Servicio) => {
    setServicioToDelete(servicio)
    setIsDeleteModalOpen(true)
  }

  const handleCloseDeleteModal = () => {
    setIsDeleteModalOpen(false)
    setServicioToDelete(null)
  }

  const handleConfirmDelete = async () => {
    if (servicioToDelete) {
      try {
        await deleteServicio(servicioToDelete.id)
        handleCloseDeleteModal()
      } catch (error) {
        console.error('Error al eliminar servicio:', error)
      }
    }
  }

  /**
   * Handler de búsqueda (SRP)
   */
  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      await searchServicios(searchQuery)
    } else {
      await fetchServicios()
    }
  }

  const handleClearSearch = () => {
    setSearchQuery('')
    fetchServicios()
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Gestión de Servicios
        </h1>
        <p className="text-gray-600">
          Administra los servicios que ofrece tu centro
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
                  placeholder="Buscar por nombre..."
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
              Nuevo Servicio
            </Button>
          </div>
        </CardBody>
      </Card>

      {/* Lista de Servicios */}
      <Card>
        <ServiciosList
          servicios={servicios}
          loading={loading}
          onEdit={handleOpenEditModal}
          onDelete={handleOpenDeleteModal}
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
            {modalMode === 'create' ? 'Nuevo Servicio' : 'Editar Servicio'}
          </h2>
        </ModalHeader>
        <ModalBody>
          <ServicioForm
            servicio={selectedServicio}
            onSubmit={handleFormSubmit}
            onCancel={handleCloseModal}
            loading={loading}
            formId="servicio-form"
            showButtons={false}
          />
        </ModalBody>
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
            form="servicio-form"
            variant="primary"
            loading={loading}
          >
            {modalMode === 'edit' ? 'Actualizar Servicio' : 'Crear Servicio'}
          </Button>
        </ModalFooter>
      </Modal>

      {/* Modal de Confirmación de Eliminación */}
      <Modal
        isOpen={isDeleteModalOpen}
        onClose={handleCloseDeleteModal}
        size="sm"
        showCloseButton={true}
      >
        <ModalHeader>
          <h2 className="text-xl font-bold text-gray-900">
            Confirmar Eliminación
          </h2>
        </ModalHeader>
        <ModalBody>
          <p className="text-gray-700">
            ¿Estás seguro que deseas eliminar el servicio{' '}
            <strong>{servicioToDelete?.nombre}</strong>?
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
