import { useState, useEffect } from 'react'
import Modal, { ModalHeader, ModalBody, ModalFooter } from '@/components/ui/Modal/Modal'
import Input from '@/components/ui/Input/Input'
import Select from '@/components/ui/Select/Select'
import Button from '@/components/ui/Button/Button'
import { venderProducto } from '@/services/miCajaService'
import { getClientes } from '@/services/clienteService'
import api from '@/services/api'
import { PaymentMethod, type Producto, type Cliente } from '@/types/models'
import { PAYMENT_METHOD_LABELS } from '@/types/miCaja'

interface VenderProductoModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

const VenderProductoModal = ({ isOpen, onClose, onSuccess }: VenderProductoModalProps) => {
  const [productos, setProductos] = useState<Producto[]>([])
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [loading, setLoading] = useState(false)
  const [loadingData, setLoadingData] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [productoId, setProductoId] = useState<number | ''>('')
  const [cantidad, setCantidad] = useState<number>(1)
  const [clienteId, setClienteId] = useState<number | ''>('')
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>(PaymentMethod.CASH)
  const [descuentoPorcentaje, setDescuentoPorcentaje] = useState<number>(0)

  // Calculated values
  const [subtotal, setSubtotal] = useState(0)
  const [descuentoMonto, setDescuentoMonto] = useState(0)
  const [total, setTotal] = useState(0)

  // Load products and clients when modal opens
  useEffect(() => {
    if (isOpen) {
      loadData()
    }
  }, [isOpen])

  // Calculate totals when product, quantity, or discount changes
  useEffect(() => {
    if (productoId && cantidad > 0) {
      const producto = productos.find(p => p.id === productoId)
      if (producto) {
        const sub = producto.precio_venta * cantidad
        const desc = (sub * descuentoPorcentaje) / 100
        const tot = sub - desc

        setSubtotal(sub)
        setDescuentoMonto(desc)
        setTotal(tot)
      }
    } else {
      setSubtotal(0)
      setDescuentoMonto(0)
      setTotal(0)
    }
  }, [productoId, cantidad, descuentoPorcentaje, productos])

  const loadData = async () => {
    try {
      setLoadingData(true)
      setError(null)

      // Load products (active with stock)
      const productosResponse = await api.get('/inventario/productos/', {
        params: { activo: true, stock_minimo: 1 }
      })
      setProductos(productosResponse.data.results || productosResponse.data || [])

      // Load clients
      const clientesData = await getClientes({ activo: true })
      setClientes(clientesData.results || [])
    } catch (err: any) {
      console.error('Error loading data:', err)
      setError('Error al cargar productos y clientes')
    } finally {
      setLoadingData(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!productoId) {
      setError('Debe seleccionar un producto')
      return
    }

    if (!clienteId) {
      setError('Debe seleccionar un cliente')
      return
    }

    if (cantidad <= 0) {
      setError('La cantidad debe ser mayor a 0')
      return
    }

    // Validate stock
    const producto = productos.find(p => p.id === productoId)
    if (producto && cantidad > producto.stock_actual) {
      setError(`Stock insuficiente. Disponible: ${producto.stock_actual}`)
      return
    }

    try {
      setLoading(true)
      setError(null)

      await venderProducto({
        producto_id: productoId as number,
        cantidad,
        cliente_id: clienteId as number,
        payment_method: paymentMethod,
        descuento_porcentaje: descuentoPorcentaje
      })

      // Reset form and close modal
      resetForm()
      onSuccess()
      onClose()
    } catch (err: any) {
      console.error('Error selling product:', err)
      setError(err.response?.data?.error || 'Error al registrar la venta')
    } finally {
      setLoading(false)
    }
  }

  const resetForm = () => {
    setProductoId('')
    setCantidad(1)
    setClienteId('')
    setPaymentMethod(PaymentMethod.CASH)
    setDescuentoPorcentaje(0)
    setError(null)
  }

  const handleClose = () => {
    resetForm()
    onClose()
  }

  const paymentMethodOptions = Object.entries(PAYMENT_METHOD_LABELS).map(([value, label]) => ({
    value,
    label
  }))

  const productoOptions = productos.map(producto => ({
    value: producto.id.toString(),
    label: `${producto.nombre} - Stock: ${producto.stock_actual} - $${producto.precio_venta}`
  }))

  const clienteOptions = clientes.map(cliente => ({
    value: cliente.id.toString(),
    label: `${cliente.nombre} ${cliente.apellido}`
  }))

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="lg">
      <ModalHeader>
        <h2 className="text-xl font-bold text-gray-800">Vender Producto</h2>
      </ModalHeader>

      <form onSubmit={handleSubmit}>
        <ModalBody>
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {loadingData ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <Select
                    label="Producto"
                    value={productoId.toString()}
                    onChange={(e) => setProductoId(e.target.value ? parseInt(e.target.value) : '')}
                    options={[
                      { value: '', label: 'Seleccione un producto...' },
                      ...productoOptions
                    ]}
                    required
                  />
                </div>

                <Input
                  label="Cantidad"
                  type="number"
                  min="1"
                  value={cantidad}
                  onChange={(e) => setCantidad(parseInt(e.target.value) || 1)}
                  required
                />

                <Input
                  label="Descuento %"
                  type="number"
                  step="0.01"
                  min="0"
                  max="100"
                  value={descuentoPorcentaje}
                  onChange={(e) => setDescuentoPorcentaje(parseFloat(e.target.value) || 0)}
                />
              </div>

              <Select
                label="Cliente"
                value={clienteId.toString()}
                onChange={(e) => setClienteId(e.target.value ? parseInt(e.target.value) : '')}
                options={[
                  { value: '', label: 'Seleccione un cliente...' },
                  ...clienteOptions
                ]}
                required
              />

              <Select
                label="Método de Pago"
                value={paymentMethod}
                onChange={(e) => setPaymentMethod(e.target.value as PaymentMethod)}
                options={paymentMethodOptions}
                required
              />

              {/* Totals Summary */}
              {productoId && (
                <div className="mt-6 p-4 bg-gray-50 rounded-md space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Subtotal:</span>
                    <span className="font-medium">${subtotal.toFixed(2)}</span>
                  </div>
                  {descuentoPorcentaje > 0 && (
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Descuento ({descuentoPorcentaje}%):</span>
                      <span className="font-medium text-red-600">-${descuentoMonto.toFixed(2)}</span>
                    </div>
                  )}
                  <div className="flex justify-between text-lg font-bold pt-2 border-t border-gray-300">
                    <span>Total:</span>
                    <span className="text-green-600">${total.toFixed(2)}</span>
                  </div>
                </div>
              )}
            </div>
          )}
        </ModalBody>

        <ModalFooter>
          <Button
            type="button"
            variant="secondary"
            onClick={handleClose}
            disabled={loading}
          >
            Cancelar
          </Button>
          <Button
            type="submit"
            variant="primary"
            disabled={loading || loadingData}
          >
            {loading ? 'Registrando...' : 'Registrar Venta'}
          </Button>
        </ModalFooter>
      </form>
    </Modal>
  )
}

export default VenderProductoModal
