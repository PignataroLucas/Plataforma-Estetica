import { useState, useEffect } from 'react'
import Modal, { ModalHeader, ModalBody, ModalFooter } from '@/components/ui/Modal/Modal'
import Input from '@/components/ui/Input/Input'
import Button from '@/components/ui/Button/Button'
import { DateInput } from '@/components/ui/DateInput/DateInput'
import { cerrarCaja, getResumenDia } from '@/services/miCajaService'
import type { ResumenDiario } from '@/types/miCaja'

interface CierreCajaModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

const CierreCajaModal = ({ isOpen, onClose, onSuccess }: CierreCajaModalProps) => {
  const [loading, setLoading] = useState(false)
  const [loadingResumen, setLoadingResumen] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Form fields
  const [fecha, setFecha] = useState<string>(new Date().toISOString().split('T')[0])
  const [efectivoContado, setEfectivoContado] = useState<number>(0)
  const [notas, setNotas] = useState('')

  // System summary data
  const [resumen, setResumen] = useState<ResumenDiario | null>(null)
  const [diferencia, setDiferencia] = useState<number>(0)

  // Helper to safely convert to number
  const toNumber = (value: number | string): number => {
    return typeof value === 'string' ? parseFloat(value) : value
  }

  // Helper to format currency
  const formatCurrency = (amount: number | string): string => {
    const numAmount = toNumber(amount)
    if (isNaN(numAmount)) return '$0.00'
    return `$${numAmount.toFixed(2)}`
  }

  // Load day summary when modal opens or date changes
  useEffect(() => {
    if (isOpen) {
      loadResumenDia()
    }
  }, [isOpen, fecha])

  // Calculate difference when cash counted changes
  useEffect(() => {
    if (resumen) {
      const efectivoSistema = toNumber(resumen.por_metodo['Efectivo'] || 0)
      const diff = efectivoContado - efectivoSistema
      setDiferencia(diff)
    }
  }, [efectivoContado, resumen])

  const loadResumenDia = async () => {
    try {
      setLoadingResumen(true)
      setError(null)
      const data = await getResumenDia(fecha)
      setResumen(data)

      // Check if already closed
      if (data.tiene_cierre) {
        setError('Ya existe un cierre de caja para esta fecha')
      }
    } catch (err: any) {
      console.error('Error loading daily summary:', err)
      setError('Error al cargar resumen del día')
    } finally {
      setLoadingResumen(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!resumen) {
      setError('Debe cargar el resumen del día primero')
      return
    }

    if (resumen.tiene_cierre) {
      setError('Ya existe un cierre de caja para esta fecha')
      return
    }

    if (efectivoContado < 0) {
      setError('El efectivo contado no puede ser negativo')
      return
    }

    try {
      setLoading(true)
      setError(null)

      const response = await cerrarCaja({
        fecha,
        efectivo_contado: efectivoContado,
        notas
      })

      // Show alert if there's a significant difference
      if (response.alerta) {
        alert('⚠️ Atención: Existe una diferencia significativa en el cierre de caja')
      }

      // Reset form and close modal
      resetForm()
      onSuccess()
      onClose()
    } catch (err: any) {
      console.error('Error creating cash closing:', err)
      setError(err.response?.data?.error || 'Error al registrar cierre de caja')
    } finally {
      setLoading(false)
    }
  }

  const resetForm = () => {
    setFecha(new Date().toISOString().split('T')[0])
    setEfectivoContado(0)
    setNotas('')
    setError(null)
    setResumen(null)
  }

  const handleClose = () => {
    resetForm()
    onClose()
  }

  const getDiferenciaColor = () => {
    if (diferencia === 0) return 'text-gray-600'
    if (Math.abs(diferencia) < 100) return 'text-yellow-600'
    return diferencia > 0 ? 'text-green-600' : 'text-red-600'
  }

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="lg">
      <ModalHeader>
        <h2 className="text-xl font-bold text-gray-800">Cierre de Caja</h2>
      </ModalHeader>

      <form onSubmit={handleSubmit}>
        <ModalBody>
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <div className="space-y-4">
            <DateInput
              label="Fecha de Cierre"
              value={fecha}
              onChange={setFecha}
              max={new Date().toISOString().split('T')[0]}
              required
            />

            {loadingResumen ? (
              <div className="flex justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : resumen && !resumen.tiene_cierre ? (
              <>
                {/* System Summary */}
                <div className="p-4 bg-blue-50 rounded-md space-y-3">
                  <h3 className="font-semibold text-gray-800 mb-2">Resumen del Sistema</h3>

                  <div className="flex justify-between">
                    <span className="text-gray-600">Total del Día:</span>
                    <span className="font-bold text-blue-600">{formatCurrency(resumen.total)}</span>
                  </div>

                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Transacciones:</span>
                    <span className="font-medium">{resumen.cantidad_transacciones}</span>
                  </div>

                  {/* Breakdown by payment method */}
                  <div className="mt-3 pt-3 border-t border-blue-200">
                    <p className="text-sm font-medium text-gray-700 mb-2">Desglose por Método:</p>
                    <div className="space-y-1">
                      {Object.entries(resumen.por_metodo).map(([metodo, monto]) => (
                        <div key={metodo} className="flex justify-between text-sm">
                          <span className="text-gray-600">{metodo}:</span>
                          <span className="font-medium">{formatCurrency(monto)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Cash Count Input */}
                <Input
                  label="Efectivo Contado (físico)"
                  type="number"
                  step="0.01"
                  min="0"
                  value={efectivoContado}
                  onChange={(e) => setEfectivoContado(parseFloat(e.target.value) || 0)}
                  placeholder="0.00"
                  required
                  helperText="Ingrese el monto de efectivo contado físicamente en caja"
                />

                {/* Difference Calculation */}
                {efectivoContado > 0 && (
                  <div className="p-4 bg-gray-50 rounded-md">
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="text-sm text-gray-600">Efectivo Sistema:</p>
                        <p className="font-medium">{formatCurrency(resumen.por_metodo['Efectivo'] || 0)}</p>
                      </div>
                      <div className="text-center">
                        <p className="text-sm text-gray-600">Diferencia:</p>
                        <p className={`text-xl font-bold ${getDiferenciaColor()}`}>
                          {diferencia > 0 ? '+' : ''}{formatCurrency(Math.abs(diferencia))}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-gray-600">Efectivo Contado:</p>
                        <p className="font-medium">{formatCurrency(efectivoContado)}</p>
                      </div>
                    </div>
                    {Math.abs(diferencia) >= 100 && (
                      <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded">
                        <p className="text-xs text-yellow-800">
                          ⚠️ Diferencia significativa detectada. Por favor, verifique el conteo.
                        </p>
                      </div>
                    )}
                  </div>
                )}

                {/* Notes */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Notas (opcional)
                  </label>
                  <textarea
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    rows={3}
                    value={notas}
                    onChange={(e) => setNotas(e.target.value)}
                    placeholder="Observaciones sobre el cierre..."
                  />
                </div>
              </>
            ) : resumen?.tiene_cierre ? (
              <div className="text-center py-8">
                <p className="text-gray-500">Esta fecha ya tiene un cierre de caja registrado</p>
              </div>
            ) : null}
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
            variant="primary"
            disabled={loading || loadingResumen || !resumen || resumen.tiene_cierre}
          >
            {loading ? 'Registrando...' : 'Cerrar Caja'}
          </Button>
        </ModalFooter>
      </form>
    </Modal>
  )
}

export default CierreCajaModal
