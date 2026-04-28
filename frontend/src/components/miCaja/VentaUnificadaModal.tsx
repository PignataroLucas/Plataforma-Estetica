import { useState, useEffect } from 'react'
import Modal, { ModalHeader, ModalBody, ModalFooter } from '@/components/ui/Modal/Modal'
import Input from '@/components/ui/Input/Input'
import Select from '@/components/ui/Select/Select'
import SearchSelect from '@/components/ui/SearchSelect/SearchSelect'
import Button from '@/components/ui/Button/Button'
import { registrarVentaUnificada, getTurnosPendientesCobro } from '@/services/miCajaService'
import { getClientes } from '@/services/clienteService'
import api from '@/services/api'
import { PaymentMethod, type Producto, type Cliente, type Servicio } from '@/types/models'
import { PAYMENT_METHOD_LABELS, type TurnoPendienteCobro, type VentaUnificadaItem } from '@/types/miCaja'

interface VentaUnificadaModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

interface CartItem {
  id: string
  tipo: 'producto' | 'servicio' | 'servicio_directo'
  producto_id?: number
  turno_id?: number
  servicio_id?: number
  nombre: string
  cantidad: number
  precio_unitario: number
  descuento_porcentaje: number
  subtotal: number
  total: number
}

type ItemTipo = 'producto' | 'servicio' | 'servicio_directo'

const VentaUnificadaModal = ({ isOpen, onClose, onSuccess }: VentaUnificadaModalProps) => {
  const [productos, setProductos] = useState<Producto[]>([])
  const [turnos, setTurnos] = useState<TurnoPendienteCobro[]>([])
  const [servicios, setServicios] = useState<Servicio[]>([])
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [loading, setLoading] = useState(false)
  const [loadingData, setLoadingData] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Sale-wide settings
  const [clienteId, setClienteId] = useState<number | null>(null)
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>(PaymentMethod.CASH)
  const [notas, setNotas] = useState('')

  // Cart
  const [cart, setCart] = useState<CartItem[]>([])

  // Add item form
  const [itemTipo, setItemTipo] = useState<ItemTipo>('producto')
  const [selectedProducto, setSelectedProducto] = useState<number | ''>('')
  const [selectedTurno, setSelectedTurno] = useState<number | ''>('')
  const [selectedServicio, setSelectedServicio] = useState<number | ''>('')
  const [cantidad, setCantidad] = useState(1)
  const [precioUnitario, setPrecioUnitario] = useState<number | ''>('')
  const [descuento, setDescuento] = useState(0)

  useEffect(() => {
    if (isOpen) {
      loadData()
    }
  }, [isOpen])

  // Auto-fill price when product is selected
  useEffect(() => {
    if (selectedProducto) {
      const producto = productos.find(p => p.id === selectedProducto)
      if (producto) {
        setPrecioUnitario(Number(producto.precio_venta))
      }
    } else {
      setPrecioUnitario('')
    }
  }, [selectedProducto, productos])

  // Auto-fill price when service is selected
  useEffect(() => {
    if (selectedServicio) {
      const servicio = servicios.find(s => s.id === selectedServicio)
      if (servicio) {
        setPrecioUnitario(Number(servicio.precio))
      }
    } else if (itemTipo === 'servicio_directo') {
      setPrecioUnitario('')
    }
  }, [selectedServicio, servicios, itemTipo])

  // Auto-fill price when turno is selected (pending amount)
  useEffect(() => {
    if (selectedTurno && itemTipo === 'servicio') {
      const turno = turnos.find(t => t.id === selectedTurno)
      if (turno) {
        const montoPendiente = typeof turno.monto === 'string' ? parseFloat(turno.monto) : Number(turno.monto)
        setPrecioUnitario(montoPendiente)
      }
    } else if (!selectedTurno && itemTipo === 'servicio') {
      setPrecioUnitario('')
    }
  }, [selectedTurno, turnos, itemTipo])

  const loadData = async () => {
    try {
      setLoadingData(true)
      setError(null)

      const [productosResponse, turnosData, clientesData, serviciosResponse] = await Promise.all([
        api.get('/inventario/productos/', { params: { activo: true } }),
        getTurnosPendientesCobro(),
        getClientes({ activo: true, page_size: 1000 }),
        api.get('/servicios/servicios/', { params: { activo: true } })
      ])

      const productosData = productosResponse.data.results || productosResponse.data || []
      const productosConStock = productosData.filter((p: Producto) => p.stock_actual > 0)

      const serviciosData = serviciosResponse.data.results || serviciosResponse.data || []
      const serviciosActivos = serviciosData.filter((s: Servicio) => s.activo)

      const clientesList = (clientesData.results || []).slice().sort((a: Cliente, b: Cliente) => {
        const nombreA = `${a.nombre} ${a.apellido}`.toLocaleLowerCase('es')
        const nombreB = `${b.nombre} ${b.apellido}`.toLocaleLowerCase('es')
        return nombreA.localeCompare(nombreB, 'es')
      })

      setProductos(productosConStock)
      setTurnos(turnosData.turnos || [])
      setClientes(clientesList)
      setServicios(serviciosActivos)
    } catch (err: any) {
      console.error('Error loading data:', err)
      setError('Error al cargar datos')
    } finally {
      setLoadingData(false)
    }
  }

  const agregarItem = () => {
    try {
      setError(null)

      if (itemTipo === 'producto') {
        if (!selectedProducto) {
          setError('Seleccione un producto')
          return
        }

        const producto = productos.find(p => p.id === selectedProducto)
        if (!producto) {
          setError('Producto no encontrado')
          return
        }

        const precio = precioUnitario !== '' ? Number(precioUnitario) : Number(producto.precio_venta)
        if (!precio || precio <= 0) {
          setError('El precio debe ser mayor a 0')
          return
        }

        if (cantidad <= 0) {
          setError('La cantidad debe ser mayor a 0')
          return
        }

        if (cantidad > producto.stock_actual) {
          setError(`Stock insuficiente. Disponible: ${producto.stock_actual}`)
          return
        }

        const subtotal = precio * Number(cantidad)
        const descuentoMonto = (subtotal * Number(descuento)) / 100
        const total = subtotal - descuentoMonto

        const newItem: CartItem = {
          id: `producto-${Date.now()}-${Math.random()}`,
          tipo: 'producto',
          producto_id: producto.id,
          nombre: `${producto.nombre} (x${cantidad})`,
          cantidad: Number(cantidad),
          precio_unitario: precio,
          descuento_porcentaje: Number(descuento),
          subtotal,
          total
        }

        setCart([...cart, newItem])
        setSelectedProducto('')
        setCantidad(1)
        setPrecioUnitario('')
        setDescuento(0)

      } else if (itemTipo === 'servicio') {
        if (!selectedTurno) {
          setError('Seleccione un turno')
          return
        }

        const turno = turnos.find(t => t.id === selectedTurno)
        if (!turno) {
          setError('Turno no encontrado')
          return
        }

        if (cart.some(item => item.turno_id === turno.id)) {
          setError('Este turno ya está en el carrito')
          return
        }

        const montoPendiente = typeof turno.monto === 'string' ? parseFloat(turno.monto) : Number(turno.monto)
        const montoSena = typeof turno.monto_sena === 'string' ? parseFloat(turno.monto_sena) : Number(turno.monto_sena)
        const esConSena = montoSena > 0

        const importeACobrar = precioUnitario !== '' ? Number(precioUnitario) : montoPendiente
        if (!importeACobrar || importeACobrar <= 0) {
          setError('El importe a cobrar debe ser mayor a 0')
          return
        }

        // Apply discount if any
        const descuentoMonto = (importeACobrar * Number(descuento)) / 100
        const totalConDescuento = importeACobrar - descuentoMonto

        const importeModificado = importeACobrar !== montoPendiente
        const nombreBase = esConSena
          ? `${turno.servicio} - ${turno.cliente} (SALDO - Seña: $${montoSena.toFixed(2)})`
          : `${turno.servicio} - ${turno.cliente}`

        const newItem: CartItem = {
          id: `servicio-${Date.now()}-${Math.random()}`,
          tipo: 'servicio',
          turno_id: turno.id,
          nombre: importeModificado ? `${nombreBase} [importe modificado]` : nombreBase,
          cantidad: 1,
          precio_unitario: importeACobrar,
          descuento_porcentaje: Number(descuento),
          subtotal: importeACobrar,
          total: totalConDescuento
        }

        setCart([...cart, newItem])
        setSelectedTurno('')
        setPrecioUnitario('')
        setDescuento(0)

      } else if (itemTipo === 'servicio_directo') {
        if (!selectedServicio) {
          setError('Seleccione un servicio')
          return
        }

        const servicio = servicios.find(s => s.id === selectedServicio)
        if (!servicio) {
          setError('Servicio no encontrado')
          return
        }

        const precio = precioUnitario !== '' ? Number(precioUnitario) : Number(servicio.precio)
        if (!precio || precio <= 0) {
          setError('El precio debe ser mayor a 0')
          return
        }

        const subtotal = precio
        const descuentoMonto = (subtotal * Number(descuento)) / 100
        const total = subtotal - descuentoMonto

        const newItem: CartItem = {
          id: `servicio_directo-${Date.now()}-${Math.random()}`,
          tipo: 'servicio_directo',
          servicio_id: servicio.id,
          nombre: `${servicio.nombre} (directo)`,
          cantidad: 1,
          precio_unitario: precio,
          descuento_porcentaje: Number(descuento),
          subtotal,
          total
        }

        setCart([...cart, newItem])
        setSelectedServicio('')
        setPrecioUnitario('')
        setDescuento(0)
      }
    } catch (err: any) {
      console.error('Error al agregar item:', err)
      setError('Error al agregar el item al carrito')
    }
  }

  const eliminarItem = (itemId: string) => {
    setCart(cart.filter(item => item.id !== itemId))
  }

  const calcularTotalGeneral = () => {
    return cart.reduce((sum, item) => sum + item.total, 0)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (cart.length === 0) {
      setError('Agregue al menos un item al carrito')
      return
    }

    try {
      setLoading(true)
      setError(null)

      const items: VentaUnificadaItem[] = cart.map(item => {
        const ventaItem: VentaUnificadaItem = {
          tipo: item.tipo,
          cantidad: item.cantidad,
          descuento_porcentaje: item.descuento_porcentaje
        }

        if (item.tipo === 'producto') {
          ventaItem.producto_id = item.producto_id
          ventaItem.precio_unitario = item.precio_unitario
        } else if (item.tipo === 'servicio') {
          ventaItem.turno_id = item.turno_id
          ventaItem.precio_unitario = item.precio_unitario
        } else if (item.tipo === 'servicio_directo') {
          ventaItem.servicio_id = item.servicio_id
          ventaItem.precio_unitario = item.precio_unitario
        }

        return ventaItem
      })

      await registrarVentaUnificada({
        items,
        cliente_id: clienteId,
        payment_method: paymentMethod,
        notas
      })

      resetForm()
      onSuccess()
      onClose()
    } catch (err: any) {
      console.error('Error registering sale:', err)

      let errorMessage = 'Error al registrar la venta'
      if (err.response?.data) {
        if (err.response.data.error) {
          errorMessage = err.response.data.error
        } else if (err.response.data.items) {
          errorMessage = JSON.stringify(err.response.data.items)
        } else if (typeof err.response.data === 'string') {
          errorMessage = err.response.data
        } else {
          errorMessage = JSON.stringify(err.response.data)
        }
      }

      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const resetForm = () => {
    setClienteId(null)
    setPaymentMethod(PaymentMethod.CASH)
    setNotas('')
    setCart([])
    setItemTipo('producto')
    setSelectedProducto('')
    setSelectedTurno('')
    setSelectedServicio('')
    setCantidad(1)
    setPrecioUnitario('')
    setDescuento(0)
    setError(null)
  }

  const handleClose = () => {
    resetForm()
    onClose()
  }

  const switchTab = (tab: ItemTipo) => {
    setItemTipo(tab)
    setSelectedProducto('')
    setSelectedTurno('')
    setSelectedServicio('')
    setPrecioUnitario('')
    setCantidad(1)
    setDescuento(0)
  }

  const paymentMethodOptions = Object.entries(PAYMENT_METHOD_LABELS).map(([value, label]) => ({
    value,
    label
  }))

  const clienteOptions = [
    { value: '', label: 'Sin cliente (consumidor final)' },
    ...clientes.map(cliente => ({
      value: cliente.id.toString(),
      label: `${cliente.nombre} ${cliente.apellido}`
    }))
  ]

  const productoOptions = productos.map(producto => ({
    value: producto.id.toString(),
    label: `${producto.nombre} - Stock: ${producto.stock_actual} - $${producto.precio_venta}`
  }))

  const servicioOptions = servicios.map(servicio => ({
    value: servicio.id.toString(),
    label: `${servicio.nombre} - $${servicio.precio}`
  }))

  const turnoOptions = turnos.map(turno => {
    const montoSena = typeof turno.monto_sena === 'string' ? parseFloat(turno.monto_sena) : turno.monto_sena
    const montoPendiente = typeof turno.monto === 'string' ? parseFloat(turno.monto) : turno.monto
    const esConSena = montoSena > 0

    return {
      value: turno.id.toString(),
      label: esConSena
        ? `${turno.servicio} - ${turno.cliente} - ${turno.fecha} ${turno.hora} - SALDO: $${montoPendiente.toFixed(2)} (Seña: $${montoSena.toFixed(2)})`
        : `${turno.servicio} - ${turno.cliente} - ${turno.fecha} ${turno.hora} - $${montoPendiente.toFixed(2)}`
    }
  })

  const tabConfig: { key: ItemTipo; label: string; color: string }[] = [
    { key: 'producto', label: 'Producto', color: 'blue' },
    { key: 'servicio', label: 'Cobrar Turno', color: 'green' },
    { key: 'servicio_directo', label: 'Servicio Directo', color: 'purple' },
  ]

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="xl">
      <ModalHeader>
        <h2 className="text-xl font-bold text-gray-800">Nueva Venta</h2>
        <p className="text-sm text-gray-500 mt-1">Productos y servicios en un solo ticket</p>
      </ModalHeader>

      <form onSubmit={handleSubmit}>
        <ModalBody className="max-h-[70vh] overflow-y-auto">
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
            <div className="space-y-6">
              {/* Cliente (opcional) y Método de Pago */}
              <div className="grid grid-cols-2 gap-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <SearchSelect
                  label="Cliente (opcional)"
                  value={clienteId?.toString() ?? ''}
                  onChange={(value) => setClienteId(value ? parseInt(value) : null)}
                  options={clienteOptions}
                  placeholder="Buscar cliente..."
                />
                <Select
                  label="Método de Pago"
                  value={paymentMethod}
                  onChange={(e) => setPaymentMethod(e.target.value as PaymentMethod)}
                  options={paymentMethodOptions}
                  required
                />
              </div>

              {/* Agregar Items */}
              <div className="border border-gray-200 rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 mb-3">Agregar Item</h3>

                <div className="space-y-3">
                  {/* Tabs */}
                  <div className="flex gap-2">
                    {tabConfig.map(tab => (
                      <button
                        key={tab.key}
                        type="button"
                        onClick={() => switchTab(tab.key)}
                        className={`flex-1 py-2 px-3 rounded-md font-medium text-sm transition-colors ${
                          itemTipo === tab.key
                            ? tab.color === 'blue' ? 'bg-blue-600 text-white'
                              : tab.color === 'green' ? 'bg-green-600 text-white'
                              : 'bg-purple-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        {tab.label}
                      </button>
                    ))}
                  </div>

                  {/* Product form */}
                  {itemTipo === 'producto' && (
                    <div className="space-y-3">
                      <div className="grid grid-cols-2 gap-3">
                        <div className="col-span-2">
                          <Select
                            label="Producto"
                            value={selectedProducto.toString()}
                            onChange={(e) => setSelectedProducto(e.target.value ? parseInt(e.target.value) : '')}
                            options={[
                              { value: '', label: 'Seleccione...' },
                              ...productoOptions
                            ]}
                          />
                        </div>
                      </div>
                      <div className="grid grid-cols-3 gap-3">
                        <Input
                          label="Precio unitario"
                          type="number"
                          step="0.01"
                          min="0.01"
                          value={precioUnitario}
                          onChange={(e) => setPrecioUnitario(e.target.value ? parseFloat(e.target.value) : '')}
                          placeholder="Precio..."
                        />
                        <Input
                          label="Cantidad"
                          type="number"
                          min="1"
                          value={cantidad}
                          onChange={(e) => setCantidad(parseInt(e.target.value) || 1)}
                        />
                        <Input
                          label="Descuento %"
                          type="number"
                          step="0.01"
                          min="0"
                          max="100"
                          value={descuento}
                          onChange={(e) => setDescuento(parseFloat(e.target.value) || 0)}
                        />
                      </div>
                    </div>
                  )}

                  {/* Service from turno */}
                  {itemTipo === 'servicio' && (
                    <div className="space-y-3">
                      <Select
                        label="Turno a Cobrar"
                        value={selectedTurno.toString()}
                        onChange={(e) => setSelectedTurno(e.target.value ? parseInt(e.target.value) : '')}
                        options={[
                          { value: '', label: 'Seleccione un turno...' },
                          ...turnoOptions
                        ]}
                      />
                      <div className="grid grid-cols-2 gap-3">
                        <Input
                          label="Importe a cobrar"
                          type="number"
                          step="0.01"
                          min="0.01"
                          value={precioUnitario}
                          onChange={(e) => setPrecioUnitario(e.target.value ? parseFloat(e.target.value) : '')}
                          placeholder="Se autocompleta del turno"
                        />
                        <Input
                          label="Descuento %"
                          type="number"
                          step="0.01"
                          min="0"
                          max="100"
                          value={descuento}
                          onChange={(e) => setDescuento(parseFloat(e.target.value) || 0)}
                        />
                      </div>
                      <p className="text-xs text-gray-500">
                        El importe se autocompleta con el monto pendiente del turno, pero puede modificarlo si el servicio realizado difiere del estimado.
                      </p>
                      {turnos.length === 0 && (
                        <p className="text-sm text-gray-500 italic">
                          No hay turnos pendientes de cobro
                        </p>
                      )}
                    </div>
                  )}

                  {/* Direct service (no turno) */}
                  {itemTipo === 'servicio_directo' && (
                    <div className="space-y-3">
                      <Select
                        label="Servicio"
                        value={selectedServicio.toString()}
                        onChange={(e) => setSelectedServicio(e.target.value ? parseInt(e.target.value) : '')}
                        options={[
                          { value: '', label: 'Seleccione un servicio...' },
                          ...servicioOptions
                        ]}
                      />
                      <div className="grid grid-cols-2 gap-3">
                        <Input
                          label="Precio"
                          type="number"
                          step="0.01"
                          min="0.01"
                          value={precioUnitario}
                          onChange={(e) => setPrecioUnitario(e.target.value ? parseFloat(e.target.value) : '')}
                          placeholder="Se autocompleta del catálogo"
                        />
                        <Input
                          label="Descuento %"
                          type="number"
                          step="0.01"
                          min="0"
                          max="100"
                          value={descuento}
                          onChange={(e) => setDescuento(parseFloat(e.target.value) || 0)}
                        />
                      </div>
                      <p className="text-xs text-gray-500">
                        Use esta opción para cobrar un servicio realizado sin turno previo. El precio se autocompleta pero puede modificarlo.
                      </p>
                    </div>
                  )}

                  <Button
                    type="button"
                    variant="secondary"
                    onClick={agregarItem}
                    className="w-full"
                  >
                    + Agregar al Carrito
                  </Button>
                </div>
              </div>

              {/* Cart */}
              {cart.length > 0 && (
                <div className="border border-gray-200 rounded-lg overflow-hidden">
                  <div className="bg-gray-50 px-4 py-2 border-b border-gray-200">
                    <h3 className="font-semibold text-gray-900">Carrito ({cart.length} items)</h3>
                  </div>
                  <div className="divide-y divide-gray-200 max-h-60 overflow-y-auto">
                    {cart.map(item => (
                      <div key={item.id} className="p-3 hover:bg-gray-50 transition-colors">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className={`px-2 py-0.5 text-xs rounded-full ${
                                item.tipo === 'producto'
                                  ? 'bg-blue-100 text-blue-800'
                                  : item.tipo === 'servicio'
                                  ? 'bg-green-100 text-green-800'
                                  : 'bg-purple-100 text-purple-800'
                              }`}>
                                {item.tipo === 'producto' ? 'Producto'
                                  : item.tipo === 'servicio' ? 'Servicio'
                                  : 'Serv. Directo'}
                              </span>
                              <span className="font-medium text-gray-900">{item.nombre}</span>
                            </div>
                            <div className="mt-1 text-sm text-gray-600">
                              ${item.precio_unitario.toFixed(2)}
                              {item.cantidad > 1 && ` x ${item.cantidad}`}
                              {item.descuento_porcentaje > 0 && (
                                <span className="ml-2 text-red-600">
                                  -{item.descuento_porcentaje}%
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="font-bold text-gray-900">${item.total.toFixed(2)}</div>
                            <button
                              type="button"
                              onClick={() => eliminarItem(item.id)}
                              className="mt-1 text-xs text-red-600 hover:text-red-800"
                            >
                              Eliminar
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="bg-gray-50 px-4 py-3 border-t-2 border-gray-300">
                    <div className="flex justify-between items-center">
                      <span className="text-lg font-bold text-gray-900">Total:</span>
                      <span className="text-2xl font-bold text-green-600">
                        ${calcularTotalGeneral().toFixed(2)}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Notes */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notas (opcional)
                </label>
                <textarea
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={2}
                  value={notas}
                  onChange={(e) => setNotas(e.target.value)}
                  placeholder="Notas adicionales..."
                />
              </div>
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
            disabled={loading || loadingData || cart.length === 0}
          >
            {loading ? 'Registrando...' : `Registrar Venta (${cart.length} items)`}
          </Button>
        </ModalFooter>
      </form>
    </Modal>
  )
}

export default VentaUnificadaModal
