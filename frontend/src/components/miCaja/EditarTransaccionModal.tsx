import { useState, useEffect } from 'react'
import Modal, { ModalHeader, ModalBody, ModalFooter } from '@/components/ui/Modal/Modal'
import Input from '@/components/ui/Input/Input'
import Select from '@/components/ui/Select/Select'
import Button from '@/components/ui/Button/Button'
import { editarTransaccion } from '@/services/miCajaService'
import { getClientes } from '@/services/clienteService'
import { PaymentMethod, type Cliente } from '@/types/models'
import { PAYMENT_METHOD_LABELS, type TransaccionMiCaja } from '@/types/miCaja'

interface EditarTransaccionModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
  transaccion: TransaccionMiCaja | null
}

const EditarTransaccionModal = ({ isOpen, onClose, onSuccess, transaccion }: EditarTransaccionModalProps) => {
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [loading, setLoading] = useState(false)
  const [loadingData, setLoadingData] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [amount, setAmount] = useState<number>(0)
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>(PaymentMethod.CASH)
  const [clienteId, setClienteId] = useState<number | null>(null)
  const [notas, setNotas] = useState('')

  useEffect(() => {
    if (isOpen && transaccion) {
      const numAmount = typeof transaccion.amount === 'string'
        ? parseFloat(transaccion.amount)
        : transaccion.amount
      setAmount(numAmount)
      setPaymentMethod(transaccion.payment_method)
      setNotas(transaccion.notes || '')
      // We don't have client ID in TransaccionMiCaja, so we reset
      setClienteId(null)
      loadClientes()
    }
  }, [isOpen, transaccion])

  const loadClientes = async () => {
    try {
      setLoadingData(true)
      const data = await getClientes({ activo: true })
      setClientes(data.results || [])
    } catch (err) {
      console.error('Error loading clients:', err)
    } finally {
      setLoadingData(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!transaccion) return

    try {
      setLoading(true)
      setError(null)

      await editarTransaccion({
        transaccion_id: transaccion.id,
        amount,
        payment_method: paymentMethod,
        notas,
        cliente_id: clienteId
      })

      onSuccess()
      onClose()
    } catch (err: any) {
      console.error('Error editing transaction:', err)
      const errorMessage = err.response?.data?.error || 'Error al editar la transacción'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
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

  if (!transaccion) return null

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="md">
      <ModalHeader>
        <h2 className="text-xl font-bold text-gray-800">Editar Transacción</h2>
        <p className="text-sm text-gray-500 mt-1">{transaccion.concepto}</p>
      </ModalHeader>

      <form onSubmit={handleSubmit}>
        <ModalBody>
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <div className="space-y-4">
            <Input
              label="Monto"
              type="number"
              step="0.01"
              min="0.01"
              value={amount}
              onChange={(e) => setAmount(parseFloat(e.target.value) || 0)}
              required
            />

            <Select
              label="Método de Pago"
              value={paymentMethod}
              onChange={(e) => setPaymentMethod(e.target.value as PaymentMethod)}
              options={paymentMethodOptions}
              required
            />

            <Select
              label="Cliente (opcional)"
              value={clienteId?.toString() ?? ''}
              onChange={(e) => setClienteId(e.target.value ? parseInt(e.target.value) : null)}
              options={clienteOptions}
              disabled={loadingData}
            />

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Notas
              </label>
              <textarea
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={3}
                value={notas}
                onChange={(e) => setNotas(e.target.value)}
                placeholder="Notas..."
              />
            </div>
          </div>
        </ModalBody>

        <ModalFooter>
          <Button
            type="button"
            variant="secondary"
            onClick={onClose}
            disabled={loading}
          >
            Cancelar
          </Button>
          <Button
            type="submit"
            variant="primary"
            disabled={loading}
          >
            {loading ? 'Guardando...' : 'Guardar Cambios'}
          </Button>
        </ModalFooter>
      </form>
    </Modal>
  )
}

export default EditarTransaccionModal
