import { useEffect, useState } from 'react'
import { Card, Button, Input, Select, Modal, ModalHeader, ModalBody, ModalFooter } from '../components/ui'
import { ProductosList } from '../components/productos/ProductosList'
import { ProductoForm } from '../components/productos/ProductoForm'
import { useProductos } from '../hooks/useProductos'
import type { ProductoList, Producto, TipoMovimiento } from '../types/models'

type TabType = 'todos' | 'stock-bajo'

export default function InventarioPage() {
  const {
    productos,
    loading,
    error,
    fetchProductos,
    createProducto,
    updateProducto,
    deleteProducto,
    ajustarStock,
    fetchStockBajo,
    clearError,
  } = useProductos()

  const [activeTab, setActiveTab] = useState<TabType>('todos')
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
  const [isStockModalOpen, setIsStockModalOpen] = useState(false)
  const [selectedProducto, setSelectedProducto] = useState<ProductoList | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterTipo, setFilterTipo] = useState('')
  const [filterCategoria, setFilterCategoria] = useState('')
  const [filterActivo, setFilterActivo] = useState('true')

  // Estado para ajuste de stock
  const [stockAjuste, setStockAjuste] = useState({
    tipo_movimiento: 'ENTRADA' as TipoMovimiento,
    cantidad: 0,
    motivo: '',
    notas: '',
    costo_unitario: undefined as number | undefined,
  })

  useEffect(() => {
    loadProductos()
  }, [activeTab, filterTipo, filterCategoria, filterActivo])

  const loadProductos = async () => {
    if (activeTab === 'stock-bajo') {
      const productos = await fetchStockBajo()
      // fetchStockBajo retorna los productos pero no los setea en el estado
      // Necesitamos usar fetchProductos con filtros si queremos usar el estado
      return
    }

    const params: any = {}
    if (filterTipo) params.tipo = filterTipo
    if (filterCategoria) params.categoria = filterCategoria
    if (filterActivo) params.activo = filterActivo === 'true'

    fetchProductos(params)
  }

  const handleCreateProducto = async (data: Partial<Producto>) => {
    try {
      await createProducto(data)
      setIsCreateModalOpen(false)
      loadProductos()
    } catch (err) {
      console.error('Error creating producto:', err)
    }
  }

  const handleEditProducto = async (data: Partial<Producto>) => {
    if (!selectedProducto) return

    try {
      await updateProducto(selectedProducto.id, data)
      setIsEditModalOpen(false)
      setSelectedProducto(null)
      loadProductos()
    } catch (err) {
      console.error('Error updating producto:', err)
    }
  }

  const handleDeleteProducto = async () => {
    if (!selectedProducto) return

    const success = await deleteProducto(selectedProducto.id)
    if (success) {
      setIsDeleteModalOpen(false)
      setSelectedProducto(null)
      loadProductos()
    }
  }

  const handleAjustarStock = async () => {
    if (!selectedProducto) return

    const success = await ajustarStock(selectedProducto.id, stockAjuste)
    if (success) {
      setIsStockModalOpen(false)
      setSelectedProducto(null)
      setStockAjuste({
        tipo_movimiento: 'ENTRADA',
        cantidad: 0,
        motivo: '',
        notas: '',
        costo_unitario: undefined,
      })
      loadProductos()
    }
  }

  const openEditModal = (producto: ProductoList) => {
    clearError()
    setSelectedProducto(producto)
    setIsEditModalOpen(true)
  }

  const openDeleteModal = (producto: ProductoList) => {
    setSelectedProducto(producto)
    setIsDeleteModalOpen(true)
  }

  const openStockModal = (producto: ProductoList) => {
    clearError()
    setSelectedProducto(producto)
    setStockAjuste({
      tipo_movimiento: 'ENTRADA',
      cantidad: 0,
      motivo: '',
      notas: '',
      costo_unitario: producto.precio_costo,
    })
    setIsStockModalOpen(true)
  }

  const filteredProductos = productos.filter(producto => {
    if (!searchTerm) return true
    const search = searchTerm.toLowerCase()
    return (
      producto.nombre?.toLowerCase().includes(search) ||
      producto.marca?.toLowerCase().includes(search) ||
      producto.sku?.toLowerCase().includes(search) ||
      producto.codigo_barras?.toLowerCase().includes(search)
    )
  })

  const getTipoMovimientoLabel = (tipo: string) => {
    const labels: Record<string, string> = {
      ENTRADA: 'Entrada',
      SALIDA: 'Salida',
      AJUSTE: 'Ajuste',
      TRANSFERENCIA_IN: 'Transferencia Entrada',
      TRANSFERENCIA_OUT: 'Transferencia Salida',
    }
    return labels[tipo] || tipo
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Inventario de Productos</h1>
          <p className="text-gray-600 mt-1">Gestiona tus productos y stock</p>
        </div>
        <Button
          variant="primary"
          onClick={() => {
            clearError()
            setIsCreateModalOpen(true)
          }}
        >
          + Nuevo Producto
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 border-b border-gray-200 bg-white rounded-t-lg px-4">
        <button
          onClick={() => setActiveTab('todos')}
          className={`px-6 py-3 text-sm font-medium transition-colors border-b-2 ${
            activeTab === 'todos'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          }`}
        >
          📦 Todos los Productos
        </button>
        <button
          onClick={() => setActiveTab('stock-bajo')}
          className={`px-6 py-3 text-sm font-medium transition-colors border-b-2 ${
            activeTab === 'stock-bajo'
              ? 'border-red-500 text-red-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          }`}
        >
          ⚠️ Stock Bajo
        </button>
      </div>

      <Card className="rounded-t-none">
        {/* Filtros */}
        <div className="p-4 border-b border-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Input
              type="search"
              placeholder="Buscar por nombre, marca, SKU..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />

            <Select
              value={filterTipo}
              onChange={(e) => setFilterTipo(e.target.value)}
              options={[
                { value: '', label: 'Todos los tipos' },
                { value: 'REVENTA', label: 'Reventa' },
                { value: 'USO_INTERNO', label: 'Uso Interno' },
                { value: 'INSUMO', label: 'Insumo' },
              ]}
            />

            <select
              value={filterCategoria}
              onChange={(e) => setFilterCategoria(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todas las categorías</option>
              {/* TODO: Cargar categorías dinámicamente */}
            </select>

            <Select
              value={filterActivo}
              onChange={(e) => setFilterActivo(e.target.value)}
              options={[
                { value: '', label: 'Todos los estados' },
                { value: 'true', label: 'Activos' },
                { value: 'false', label: 'Inactivos' },
              ]}
            />
          </div>
        </div>

        {/* Lista de productos */}
        <div className="p-6">
          <ProductosList
            productos={filteredProductos}
            onEdit={openEditModal}
            onDelete={openDeleteModal}
            onAjustarStock={openStockModal}
            loading={loading}
          />
        </div>
      </Card>

      {/* Modal de Crear */}
      <Modal isOpen={isCreateModalOpen} onClose={() => setIsCreateModalOpen(false)} size="lg">
        <ModalHeader>Nuevo Producto</ModalHeader>
        <ModalBody>
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 text-red-700 rounded-md whitespace-pre-line">
              {error}
            </div>
          )}
          <ProductoForm
            formId="create-producto-form"
            onSubmit={handleCreateProducto}
            onCancel={() => setIsCreateModalOpen(false)}
          />
        </ModalBody>
        <ModalFooter>
          <Button variant="secondary" onClick={() => setIsCreateModalOpen(false)}>
            Cancelar
          </Button>
          <Button type="submit" form="create-producto-form" variant="primary">
            Crear Producto
          </Button>
        </ModalFooter>
      </Modal>

      {/* Modal de Editar */}
      <Modal isOpen={isEditModalOpen} onClose={() => setIsEditModalOpen(false)} size="lg">
        <ModalHeader>Editar Producto</ModalHeader>
        <ModalBody>
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 text-red-700 rounded-md whitespace-pre-line">
              {error}
            </div>
          )}
          {selectedProducto && (
            <ProductoForm
              formId="edit-producto-form"
              initialData={selectedProducto}
              onSubmit={handleEditProducto}
              onCancel={() => setIsEditModalOpen(false)}
              submitLabel="Actualizar"
            />
          )}
        </ModalBody>
        <ModalFooter>
          <Button variant="secondary" onClick={() => setIsEditModalOpen(false)}>
            Cancelar
          </Button>
          <Button type="submit" form="edit-producto-form" variant="primary">
            Actualizar
          </Button>
        </ModalFooter>
      </Modal>

      {/* Modal de Eliminar */}
      <Modal isOpen={isDeleteModalOpen} onClose={() => setIsDeleteModalOpen(false)}>
        <ModalHeader>Eliminar Producto</ModalHeader>
        <ModalBody>
          {selectedProducto && (
            <div>
              <p className="mb-3">
                ¿Estás seguro de que deseas eliminar el producto{' '}
                <strong>{selectedProducto.nombre}</strong>?
              </p>
              <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md text-sm text-yellow-800">
                <p className="font-semibold">⚠️ Advertencia:</p>
                <p>
                  Esta acción no se puede deshacer. Se perderá todo el historial de movimientos
                  asociado a este producto.
                </p>
              </div>
            </div>
          )}
        </ModalBody>
        <ModalFooter>
          <Button variant="secondary" onClick={() => setIsDeleteModalOpen(false)}>
            Cancelar
          </Button>
          <Button variant="danger" onClick={handleDeleteProducto}>
            Eliminar
          </Button>
        </ModalFooter>
      </Modal>

      {/* Modal de Ajustar Stock */}
      <Modal isOpen={isStockModalOpen} onClose={() => setIsStockModalOpen(false)}>
        <ModalHeader>Ajustar Stock - {selectedProducto?.nombre}</ModalHeader>
        <ModalBody>
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 text-red-700 rounded-md">
              {error}
            </div>
          )}
          {selectedProducto && (
            <div className="space-y-4">
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-md">
                <p className="text-sm text-blue-900">
                  <strong>Stock actual:</strong> {selectedProducto.stock_actual}{' '}
                  {selectedProducto.unidad_medida}
                </p>
                <p className="text-sm text-blue-900">
                  <strong>Stock mínimo:</strong> {selectedProducto.stock_minimo}{' '}
                  {selectedProducto.unidad_medida}
                </p>
              </div>

              <Select
                label="Tipo de Movimiento"
                value={stockAjuste.tipo_movimiento}
                onChange={(e) =>
                  setStockAjuste({ ...stockAjuste, tipo_movimiento: e.target.value as TipoMovimiento })
                }
                options={[
                  { value: 'ENTRADA', label: 'Entrada (Aumentar stock)' },
                  { value: 'SALIDA', label: 'Salida (Disminuir stock)' },
                  { value: 'AJUSTE', label: 'Ajuste (Corrección)' },
                ]}
                required
              />

              <Input
                label="Cantidad"
                type="number"
                step="0.01"
                min="0.01"
                value={stockAjuste.cantidad.toString()}
                onChange={(e) =>
                  setStockAjuste({ ...stockAjuste, cantidad: parseFloat(e.target.value) || 0 })
                }
                required
                placeholder="0.00"
              />

              {stockAjuste.tipo_movimiento === 'ENTRADA' && (
                <Input
                  label="Costo Unitario (opcional)"
                  type="number"
                  step="0.01"
                  min="0"
                  value={stockAjuste.costo_unitario?.toString() || ''}
                  onChange={(e) =>
                    setStockAjuste({
                      ...stockAjuste,
                      costo_unitario: e.target.value ? parseFloat(e.target.value) : undefined,
                    })
                  }
                  placeholder="Dejar vacío para usar el costo actual"
                />
              )}

              <Input
                label="Motivo"
                value={stockAjuste.motivo}
                onChange={(e) => setStockAjuste({ ...stockAjuste, motivo: e.target.value })}
                placeholder="Ej: Compra, Venta, Rotura, Inventario..."
              />

              <div>
                <label htmlFor="notas" className="block text-sm font-medium text-gray-700 mb-1">
                  Notas adicionales
                </label>
                <textarea
                  id="notas"
                  value={stockAjuste.notas}
                  onChange={(e) => setStockAjuste({ ...stockAjuste, notas: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Detalles adicionales del movimiento..."
                />
              </div>

              {/* Preview del cambio */}
              {stockAjuste.cantidad > 0 && (
                <div className="p-4 bg-green-50 border border-green-200 rounded-md">
                  <p className="text-sm text-green-900 font-semibold mb-2">
                    Vista previa del cambio:
                  </p>
                  <p className="text-sm text-green-900">
                    <strong>Operación:</strong> {getTipoMovimientoLabel(stockAjuste.tipo_movimiento)}
                  </p>
                  <p className="text-sm text-green-900">
                    <strong>Cantidad:</strong> {stockAjuste.cantidad} {selectedProducto.unidad_medida}
                  </p>
                  <p className="text-sm text-green-900">
                    <strong>Stock resultante:</strong>{' '}
                    {stockAjuste.tipo_movimiento === 'ENTRADA'
                      ? selectedProducto.stock_actual + stockAjuste.cantidad
                      : selectedProducto.stock_actual - stockAjuste.cantidad}{' '}
                    {selectedProducto.unidad_medida}
                  </p>
                </div>
              )}
            </div>
          )}
        </ModalBody>
        <ModalFooter>
          <Button variant="secondary" onClick={() => setIsStockModalOpen(false)}>
            Cancelar
          </Button>
          <Button
            variant="primary"
            onClick={handleAjustarStock}
            disabled={stockAjuste.cantidad <= 0}
          >
            Confirmar Ajuste
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  )
}
