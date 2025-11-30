import { useState, useEffect } from 'react'
import { AlquilerPendiente } from '@/types/models'
import api from '@/services/api'
import { Button } from '@/components/ui'
import AlquilerForm from './AlquilerForm'
import { formatDateArgentina } from '@/utils/dateUtils'

interface AlquilerPendientesProps {
  onAlquilerCreated?: () => void
}

const AlquilerPendientes = ({ onAlquilerCreated }: AlquilerPendientesProps) => {
  const [pendientes, setPendientes] = useState<AlquilerPendiente[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [selectedPendiente, setSelectedPendiente] = useState<AlquilerPendiente | undefined>()

  // Format date string (YYYY-MM-DD) to long format without timezone issues
  const formatDateLong = (dateString: string): string => {
    const [year, month, day] = dateString.split('-').map(Number)
    const date = new Date(year, month - 1, day)

    return date.toLocaleDateString('es-AR', {
      weekday: 'long',
      day: '2-digit',
      month: 'long',
      year: 'numeric',
    })
  }

  useEffect(() => {
    fetchPendientes()
  }, [])

  const fetchPendientes = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await api.get<AlquilerPendiente[]>('/servicios/alquileres/pendientes/')
      setPendientes(response.data)
    } catch (err) {
      console.error('Error loading pending rentals:', err)
      setError('Error al cargar alquileres pendientes')
    } finally {
      setLoading(false)
    }
  }

  const handleProgramar = (pendiente: AlquilerPendiente) => {
    setSelectedPendiente(pendiente)
    setShowForm(true)
  }

  const handleFormSubmit = async () => {
    setShowForm(false)
    setSelectedPendiente(undefined)
    await fetchPendientes()
    if (onAlquilerCreated) {
      onAlquilerCreated()
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-32">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        {error}
      </div>
    )
  }

  if (pendientes.length === 0) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <div className="flex items-center gap-3">
          <div className="text-2xl">✓</div>
          <div>
            <p className="font-medium text-green-900">Todo en orden</p>
            <p className="text-sm text-green-700 mt-0.5">
              No hay turnos con máquinas pendientes de confirmar alquiler
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <div className="text-2xl">⚠️</div>
          <div className="flex-1">
            <h3 className="font-semibold text-amber-900 mb-1">
              Alquileres Pendientes de Confirmación
            </h3>
            <p className="text-sm text-amber-700 mb-3">
              Los siguientes turnos usan máquinas alquiladas pero no tienen un alquiler confirmado.
              Por favor, programa y confirma el alquiler para que se genere el gasto automáticamente al completar el turno.
            </p>

            <div className="space-y-3">
              {pendientes.map((pendiente, index) => (
                <div
                  key={`${pendiente.maquina_id}-${pendiente.fecha}`}
                  className="bg-white border border-amber-300 rounded-lg p-4"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-semibold text-gray-900">
                          {pendiente.maquina_nombre}
                        </h4>
                        {pendiente.estado && (
                          <span className="px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded-full">
                            {pendiente.estado}
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-gray-600 space-y-1">
                        <p>
                          📅 <strong>Fecha:</strong> {formatDateLong(pendiente.fecha)}
                        </p>
                        <p>
                          📋 <strong>Turnos programados:</strong> {pendiente.cantidad_turnos}
                        </p>
                        <p className="font-medium text-amber-700">
                          💰 Costo del alquiler: ${pendiente.costo_diario.toLocaleString('es-AR')}
                        </p>
                      </div>
                    </div>
                    <div>
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => handleProgramar(pendiente)}
                      >
                        {pendiente.alquiler_id ? 'Confirmar' : 'Programar'}
                      </Button>
                    </div>
                  </div>

                  {pendiente.estado === 'PROGRAMADO' && (
                    <div className="mt-2 text-xs text-amber-600 bg-amber-50 border border-amber-100 rounded p-2">
                      ⚠️ El alquiler está programado pero no confirmado. Confírmalo para que se genere el gasto automáticamente.
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {showForm && selectedPendiente && (
        <AlquilerForm
          maquinaId={selectedPendiente.maquina_id}
          onSubmit={handleFormSubmit}
          onCancel={() => {
            setShowForm(false)
            setSelectedPendiente(undefined)
          }}
        />
      )}
    </div>
  )
}

export default AlquilerPendientes
