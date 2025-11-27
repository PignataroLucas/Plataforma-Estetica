import { useState, useEffect } from 'react'
import Modal, { ModalHeader, ModalBody, ModalFooter } from '@/components/ui/Modal/Modal'
import Input from '@/components/ui/Input/Input'
import Select from '@/components/ui/Select/Select'
import Button from '@/components/ui/Button/Button'
import { cobrarTurno, getTurnosPendientesCobro } from '@/services/miCajaService'
import { PaymentMethod } from '@/types/models'
import { PAYMENT_METHOD_LABELS, type TurnoPendienteCobro } from '@/types/miCaja'

interface CobrarTurnoModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

const CobrarTurnoModal = ({ isOpen, onClose, onSuccess }: CobrarTurnoModalProps) => {
  const [turnosPendientes, setTurnosPendientes] = useState<TurnoPendienteCobro[]>([])
  const [loading, setLoading] = useState(false)
  const [loadingTurnos, setLoadingTurnos] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [turnoId, setTurnoId] = useState<number | ''>('')
  const [amount, setAmount] = useState<number>(0)
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>(PaymentMethod.CASH)
  const [notas, setNotas] = useState('')

  // Load pending appointments when modal opens
  useEffect(() => {
    if (isOpen) {
      loadTurnosPendientes()
    }
  }, [isOpen])

  // Update amount when turno selection changes
  useEffect(() => {
    if (turnoId) {
      const selectedTurno = turnosPendientes.find(t => t.id === turnoId)
      if (selectedTurno) {
        setAmount(selectedTurno.monto)
      }
    }
  }, [turnoId, turnosPendientes])

  const loadTurnosPendientes = async () => {
    try {
      setLoadingTurnos(true)
      setError(null)
      const data = await getTurnosPendientesCobro()
      setTurnosPendientes(data.turnos)
    } catch (err: any) {
      console.error('Error loading pending appointments:', err)
      setError('Error al cargar turnos pendientes')
    } finally {
      setLoadingTurnos(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!turnoId) {
      setError('Debe seleccionar un turno')
      return
    }

    if (amount <= 0) {
      setError('El monto debe ser mayor a 0')
      return
    }

    try {
      setLoading(true)
      setError(null)

      await cobrarTurno({
        turno_id: turnoId as number,
        amount,
        payment_method: paymentMethod,
        notas
      })

      // Reset form and close modal
      resetForm()
      onSuccess()
      onClose()
    } catch (err: any) {
      console.error('Error charging appointment:', err)
      setError(err.response?.data?.error || 'Error al registrar el cobro')
    } finally {
      setLoading(false)
    }
  }

  const resetForm = () => {
    setTurnoId('')
    setAmount(0)
    setPaymentMethod(PaymentMethod.CASH)
    setNotas('')
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

  const turnoOptions = turnosPendientes.map(turno => ({
    value: turno.id.toString(),
    label: `${turno.cliente} - ${turno.servicio} - ${turno.fecha} ${turno.hora} - $${turno.monto}`
  }))

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="md">
      <ModalHeader>
        <h2 className="text-xl font-bold text-gray-800">Cobrar Turno</h2>
      </ModalHeader>

      <form onSubmit={handleSubmit}>
        <ModalBody>
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {loadingTurnos ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : turnosPendientes.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500">No hay turnos pendientes de cobro</p>
            </div>
          ) : (
            <div className="space-y-4">
              <Select
                label="Turno a Cobrar"
                value={turnoId.toString()}
                onChange={(e) => setTurnoId(e.target.value ? parseInt(e.target.value) : '')}
                options={[
                  { value: '', label: 'Seleccione un turno...' },
                  ...turnoOptions
                ]}
                required
              />

              <Input
                label="Monto a Cobrar"
                type="number"
                step="0.01"
                min="0"
                value={amount}
                onChange={(e) => setAmount(parseFloat(e.target.value) || 0)}
                placeholder="0.00"
                required
              />

              <Select
                label="Método de Pago"
                value={paymentMethod}
                onChange={(e) => setPaymentMethod(e.target.value as PaymentMethod)}
                options={paymentMethodOptions}
                required
              />

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notas (opcional)
                </label>
                <textarea
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={3}
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
            disabled={loading || loadingTurnos || turnosPendientes.length === 0}
          >
            {loading ? 'Registrando...' : 'Registrar Cobro'}
          </Button>
        </ModalFooter>
      </form>
    </Modal>
  )
}

export default CobrarTurnoModal
