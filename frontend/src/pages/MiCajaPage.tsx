import { useState, useEffect } from 'react'
import Card, { CardHeader, CardBody } from '@/components/ui/Card/Card'
import Button from '@/components/ui/Button/Button'
import { DateInput } from '@/components/ui/DateInput/DateInput'
import VentaUnificadaModal from '@/components/miCaja/VentaUnificadaModal'
import CierreCajaModal from '@/components/miCaja/CierreCajaModal'
import {
  getMisTransacciones,
  getResumenDia,
  getTurnosPendientesCobro
} from '@/services/miCajaService'
import {
  PAYMENT_METHOD_LABELS,
  TRANSACTION_TYPE_LABELS,
  type MisTransaccionesResponse,
  type ResumenDiario,
  type TurnoPendienteCobro
} from '@/types/miCaja'

export default function MiCajaPage() {
  const [fecha, setFecha] = useState<string>(new Date().toISOString().split('T')[0])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Modal states
  const [showVentaUnificadaModal, setShowVentaUnificadaModal] = useState(false)
  const [showCierreCajaModal, setShowCierreCajaModal] = useState(false)

  // Data states
  const [transacciones, setTransacciones] = useState<MisTransaccionesResponse | null>(null)
  const [resumen, setResumen] = useState<ResumenDiario | null>(null)
  const [turnosPendientes, setTurnosPendientes] = useState<TurnoPendienteCobro[]>([])

  useEffect(() => {
    loadData()
  }, [fecha])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Load all data in parallel
      const [transaccionesData, resumenData, pendientesData] = await Promise.all([
        getMisTransacciones(fecha),
        getResumenDia(fecha),
        getTurnosPendientesCobro()
      ])

      setTransacciones(transaccionesData)
      setResumen(resumenData)
      setTurnosPendientes(pendientesData.turnos)
    } catch (err: any) {
      console.error('Error loading Mi Caja data:', err)
      setError('Error al cargar los datos')
    } finally {
      setLoading(false)
    }
  }

  const handleModalSuccess = () => {
    // Reload data after successful operation
    loadData()
  }

  const formatCurrency = (amount: number | string) => {
    const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount
    if (isNaN(numAmount)) return '$0.00'
    return `$${numAmount.toFixed(2)}`
  }

  const formatDateTime = (dateTimeString: string) => {
    const date = new Date(dateTimeString)
    return date.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Mi Caja</h1>
          <p className="text-gray-500 mt-1">
            Registra tus cobros y ventas del día
          </p>
        </div>

        <div className="flex gap-2">
          <Button
            variant="primary"
            onClick={() => setShowVentaUnificadaModal(true)}
            className="text-lg px-6"
          >
            + Nueva Venta
          </Button>
          <Button
            variant="secondary"
            onClick={() => setShowCierreCajaModal(true)}
          >
            Cerrar Caja
          </Button>
        </div>
      </div>

      {/* Alert for pending appointments */}
      {turnosPendientes.length > 0 && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-yellow-700">
                Tienes <strong>{turnosPendientes.length}</strong> turno(s) completado(s) pendiente(s) de cobro
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Date Selector and Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold text-gray-800">Seleccionar Fecha</h3>
          </CardHeader>
          <CardBody>
            <DateInput
              value={fecha}
              onChange={setFecha}
              max={new Date().toISOString().split('T')[0]}
            />
          </CardBody>
        </Card>

        {resumen && (
          <>
            <Card className="bg-gradient-to-br from-blue-50 to-blue-100">
              <CardBody className="text-center">
                <p className="text-sm text-gray-600 mb-1">Total del Día</p>
                <p className="text-3xl font-bold text-blue-600">
                  {formatCurrency(resumen.total)}
                </p>
                <p className="text-sm text-gray-500 mt-2">
                  {resumen.cantidad_transacciones} transacciones
                </p>
              </CardBody>
            </Card>

            <Card className={resumen.tiene_cierre ? 'bg-green-50' : 'bg-orange-50'}>
              <CardBody className="text-center">
                <p className="text-sm text-gray-600 mb-1">Estado de Caja</p>
                <p className={`text-xl font-bold ${resumen.tiene_cierre ? 'text-green-600' : 'text-orange-600'}`}>
                  {resumen.tiene_cierre ? 'CERRADA' : 'ABIERTA'}
                </p>
                <p className="text-sm text-gray-500 mt-2">
                  {resumen.tiene_cierre ? 'Cierre registrado' : 'Pendiente de cierre'}
                </p>
              </CardBody>
            </Card>
          </>
        )}
      </div>

      {/* Payment Method Breakdown */}
      {resumen && Object.keys(resumen.por_metodo).length > 0 && (
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold text-gray-800">Desglose por Método de Pago</h3>
          </CardHeader>
          <CardBody>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {Object.entries(resumen.por_metodo).map(([metodo, monto]) => (
                <div key={metodo} className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-600 mb-1">{metodo}</p>
                  <p className="text-lg font-bold text-gray-800">{formatCurrency(monto)}</p>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      )}

      {/* Transactions Table */}
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold text-gray-800">Mis Transacciones</h3>
        </CardHeader>
        <CardBody>
          {loading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-red-600">{error}</p>
              <Button variant="secondary" onClick={loadData} className="mt-4">
                Reintentar
              </Button>
            </div>
          ) : transacciones && transacciones.transacciones.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Hora
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tipo
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Concepto
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Cliente
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Método
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Monto
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {transacciones.transacciones.map((transaccion) => (
                    <tr key={transaccion.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatDateTime(transaccion.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                          {TRANSACTION_TYPE_LABELS[transaccion.type]}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {transaccion.concepto}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {transaccion.cliente_nombre || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {PAYMENT_METHOD_LABELS[transaccion.payment_method]}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium text-gray-900">
                        {formatCurrency(transaccion.amount)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-gray-500">No hay transacciones registradas para esta fecha</p>
            </div>
          )}
        </CardBody>
      </Card>

      {/* Modals */}
      <VentaUnificadaModal
        isOpen={showVentaUnificadaModal}
        onClose={() => setShowVentaUnificadaModal(false)}
        onSuccess={handleModalSuccess}
      />

      <CierreCajaModal
        isOpen={showCierreCajaModal}
        onClose={() => setShowCierreCajaModal(false)}
        onSuccess={handleModalSuccess}
      />
    </div>
  )
}
