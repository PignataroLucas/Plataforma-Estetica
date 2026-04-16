import { useState } from 'react'
import Modal, { ModalHeader, ModalBody, ModalFooter } from '@/components/ui/Modal/Modal'
import Button from '@/components/ui/Button/Button'
import { eliminarTransaccion } from '@/services/miCajaService'
import { TRANSACTION_TYPE_LABELS, type TransaccionMiCaja } from '@/types/miCaja'

interface EliminarTransaccionModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
  transaccion: TransaccionMiCaja | null
}

const EliminarTransaccionModal = ({ isOpen, onClose, onSuccess, transaccion }: EliminarTransaccionModalProps) => {
  const [motivo, setMotivo] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!transaccion) return

    if (motivo.trim().length < 5) {
      setError('El motivo debe tener al menos 5 caracteres')
      return
    }

    try {
      setLoading(true)
      setError(null)

      await eliminarTransaccion({
        transaccion_id: transaccion.id,
        motivo: motivo.trim()
      })

      setMotivo('')
      onSuccess()
      onClose()
    } catch (err: any) {
      console.error('Error deleting transaction:', err)
      const errorMessage = err.response?.data?.error || 'Error al eliminar la transacción'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    setMotivo('')
    setError(null)
    onClose()
  }

  if (!transaccion) return null

  const amount = typeof transaccion.amount === 'string'
    ? parseFloat(transaccion.amount)
    : transaccion.amount

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="md">
      <ModalHeader>
        <h2 className="text-xl font-bold text-red-700">Eliminar Transacción</h2>
      </ModalHeader>

      <form onSubmit={handleSubmit}>
        <ModalBody>
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800 font-medium mb-2">
              Esta acción no se puede deshacer. Se eliminará la transacción y se revertirán los cambios asociados (inventario, estado de turno).
            </p>
            <div className="text-sm text-red-700 space-y-1">
              <p><strong>Tipo:</strong> {TRANSACTION_TYPE_LABELS[transaccion.type]}</p>
              <p><strong>Concepto:</strong> {transaccion.concepto}</p>
              <p><strong>Monto:</strong> ${amount.toFixed(2)}</p>
              {transaccion.cliente_nombre && (
                <p><strong>Cliente:</strong> {transaccion.cliente_nombre}</p>
              )}
            </div>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Motivo de eliminación <span className="text-red-500">*</span>
            </label>
            <textarea
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
              rows={3}
              value={motivo}
              onChange={(e) => setMotivo(e.target.value)}
              placeholder="Explique por qué se elimina esta venta..."
              required
              minLength={5}
            />
            <p className="text-xs text-gray-500 mt-1">
              Mínimo 5 caracteres. Este motivo quedará registrado para auditoría.
            </p>
          </div>
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
            variant="danger"
            disabled={loading || motivo.trim().length < 5}
          >
            {loading ? 'Eliminando...' : 'Eliminar Transacción'}
          </Button>
        </ModalFooter>
      </form>
    </Modal>
  )
}

export default EliminarTransaccionModal
