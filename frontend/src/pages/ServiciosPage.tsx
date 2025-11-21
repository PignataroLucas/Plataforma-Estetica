import { useState, useEffect } from 'react'
import { useServicios } from '@/hooks/useServicios'
import { Servicio, MaquinaAlquilada, AlquilerMaquina } from '@/types/models'
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
import MaquinasList from '@/components/servicios/MaquinasList'
import MaquinaForm from '@/components/servicios/MaquinaForm'
import AlquileresList from '@/components/servicios/AlquileresList'
import AlquilerForm from '@/components/servicios/AlquilerForm'
import AlquilerPendientes from '@/components/servicios/AlquileresPendientes'
import api from '@/services/api'
import toast from 'react-hot-toast'

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

  // Estado de pestañas
  const [activeTab, setActiveTab] = useState<'servicios' | 'maquinas' | 'alquileres'>('servicios')

  // Estado del modal de servicios
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create')
  const [selectedServicio, setSelectedServicio] = useState<Servicio | null>(null)

  // Estado de búsqueda
  const [searchQuery, setSearchQuery] = useState('')

  // Estado del modal de confirmación de eliminación
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
  const [servicioToDelete, setServicioToDelete] = useState<Servicio | null>(null)

  // Estado para máquinas
  const [isMaquinaModalOpen, setIsMaquinaModalOpen] = useState(false)
  const [maquinaModalMode, setMaquinaModalMode] = useState<'create' | 'edit'>('create')
  const [selectedMaquina, setSelectedMaquina] = useState<MaquinaAlquilada | null>(null)
  const [maquinasRefreshKey, setMaquinasRefreshKey] = useState(0)

  // Estado para alquileres
  const [isAlquilerFormOpen, setIsAlquilerFormOpen] = useState(false)
  const [selectedMaquinaForRental, setSelectedMaquinaForRental] = useState<number | undefined>()
  const [alquileresRefreshKey, setAlquileresRefreshKey] = useState(0)

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

  /**
   * Handlers de máquinas
   */
  const handleOpenCreateMaquinaModal = () => {
    setMaquinaModalMode('create')
    setSelectedMaquina(null)
    setIsMaquinaModalOpen(true)
  }

  const handleOpenEditMaquinaModal = (maquina: MaquinaAlquilada) => {
    setMaquinaModalMode('edit')
    setSelectedMaquina(maquina)
    setIsMaquinaModalOpen(true)
  }

  const handleCloseMaquinaModal = () => {
    setIsMaquinaModalOpen(false)
    setSelectedMaquina(null)
  }

  const handleMaquinaFormSubmit = async (data: Partial<MaquinaAlquilada>) => {
    try {
      if (maquinaModalMode === 'edit' && selectedMaquina) {
        await api.patch(`/servicios/maquinas/${selectedMaquina.id}/`, data)
        toast.success('Máquina actualizada exitosamente')
      } else {
        await api.post('/servicios/maquinas/', data)
        toast.success('Máquina creada exitosamente')
      }
      handleCloseMaquinaModal()
      setMaquinasRefreshKey(prev => prev + 1)
    } catch (error) {
      console.error('Error al guardar máquina:', error)
      toast.error('Error al guardar la máquina')
    }
  }

  /**
   * Handlers de alquileres
   */
  const handleProgramarAlquiler = (maquinaId: number) => {
    setSelectedMaquinaForRental(maquinaId)
    setIsAlquilerFormOpen(true)
  }

  const handleCloseAlquilerForm = () => {
    setIsAlquilerFormOpen(false)
    setSelectedMaquinaForRental(undefined)
  }

  const handleAlquilerFormSubmit = (alquiler: AlquilerMaquina) => {
    handleCloseAlquilerForm()
    setAlquileresRefreshKey(prev => prev + 1)
    toast.success('Alquiler programado exitosamente')
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Gestión de Servicios
        </h1>
        <p className="text-gray-600">
          Administra los servicios y máquinas alquiladas de tu centro
        </p>
      </div>

      {/* Tabs */}
      <div className="mb-6 border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('servicios')}
            className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'servicios'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            💆 Servicios
          </button>
          <button
            onClick={() => setActiveTab('maquinas')}
            className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'maquinas'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            🔧 Máquinas Alquiladas
          </button>
          <button
            onClick={() => setActiveTab('alquileres')}
            className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'alquileres'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            📅 Alquileres Programados
          </button>
        </nav>
      </div>

      {/* Toolbar */}
      {activeTab === 'servicios' && (
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
      )}

      {/* Toolbar para Máquinas */}
      {activeTab === 'maquinas' && (
        <Card className="mb-6">
          <CardBody>
            <div className="flex justify-end">
              <Button
                variant="primary"
                onClick={handleOpenCreateMaquinaModal}
                leftIcon={
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                }
              >
                Nueva Máquina
              </Button>
            </div>
          </CardBody>
        </Card>
      )}

      {/* Lista de Servicios */}
      {activeTab === 'servicios' && (
        <Card>
          <ServiciosList
            servicios={servicios}
            loading={loading}
            onEdit={handleOpenEditModal}
            onDelete={handleOpenDeleteModal}
          />
        </Card>
      )}

      {/* Lista de Máquinas */}
      {activeTab === 'maquinas' && (
        <Card>
          <MaquinasList
            onEdit={handleOpenEditMaquinaModal}
            onProgramarAlquiler={handleProgramarAlquiler}
            refreshKey={maquinasRefreshKey}
          />
        </Card>
      )}

      {/* Lista de Alquileres */}
      {activeTab === 'alquileres' && (
        <div className="space-y-6">
          {/* Alerta de alquileres pendientes */}
          <AlquilerPendientes
            onAlquilerCreated={() => setAlquileresRefreshKey(prev => prev + 1)}
          />

          {/* Lista de alquileres programados */}
          <Card>
            <AlquileresList key={alquileresRefreshKey} />
          </Card>
        </div>
      )}

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

      {/* Modal Create/Edit Máquina */}
      <Modal
        isOpen={isMaquinaModalOpen}
        onClose={handleCloseMaquinaModal}
        size="md"
        showCloseButton={true}
      >
        <ModalHeader>
          <h2 className="text-xl font-bold text-gray-900">
            {maquinaModalMode === 'create' ? 'Nueva Máquina Alquilada' : 'Editar Máquina'}
          </h2>
        </ModalHeader>
        <ModalBody>
          <MaquinaForm
            maquina={selectedMaquina}
            onSubmit={handleMaquinaFormSubmit}
            onCancel={handleCloseMaquinaModal}
            loading={loading}
            formId="maquina-form"
            showButtons={false}
          />
        </ModalBody>
        <ModalFooter>
          <Button
            type="button"
            variant="secondary"
            onClick={handleCloseMaquinaModal}
            disabled={loading}
          >
            Cancelar
          </Button>
          <Button
            type="submit"
            form="maquina-form"
            variant="primary"
            loading={loading}
          >
            {maquinaModalMode === 'edit' ? 'Actualizar Máquina' : 'Crear Máquina'}
          </Button>
        </ModalFooter>
      </Modal>

      {/* Modal/Form de Alquiler */}
      {isAlquilerFormOpen && (
        <AlquilerForm
          maquinaId={selectedMaquinaForRental}
          onSubmit={handleAlquilerFormSubmit}
          onCancel={handleCloseAlquilerForm}
        />
      )}
    </div>
  )
}
