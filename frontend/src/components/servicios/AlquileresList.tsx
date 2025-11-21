import { useState, useEffect } from 'react'
import { AlquilerMaquina, EstadoAlquiler, PaginatedResponse } from '@/types/models'
import api from '@/services/api'
import { Button } from '@/components/ui'
import AlquilerForm from './AlquilerForm'

const AlquileresList = () => {
  const [alquileres, setAlquileres] = useState<AlquilerMaquina[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [selectedAlquiler, setSelectedAlquiler] = useState<AlquilerMaquina | undefined>()
  const [actionLoading, setActionLoading] = useState<number | null>(null)

  useEffect(() => {
    fetchAlquileres()
  }, [])

  const fetchAlquileres = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await api.get<PaginatedResponse<AlquilerMaquina>>('/servicios/alquileres/')
      const alquileresList = response.data && 'results' in response.data
        ? response.data.results
        : response.data as any
      setAlquileres(alquileresList)
    } catch (err) {
      console.error('Error loading rentals:', err)
      setError('Error al cargar los alquileres')
    } finally {
      setLoading(false)
    }
  }

  const handleFormSubmit = async (alquiler: AlquilerMaquina) => {
    setShowForm(false)
    setSelectedAlquiler(undefined)
    await fetchAlquileres()
  }

  const handleEdit = (alquiler: AlquilerMaquina) => {
    setSelectedAlquiler(alquiler)
    setShowForm(true)
  }

  const handleConfirm = async (alquiler: AlquilerMaquina) => {
    if (!confirm(`¿Confirmar el alquiler de ${alquiler.maquina_nombre} para el ${new Date(alquiler.fecha).toLocaleDateString('es-AR')}?`)) {
      return
    }

    setActionLoading(alquiler.id)
    try {
      await api.post(`/servicios/alquileres/${alquiler.id}/confirmar/`)
      await fetchAlquileres()
    } catch (err: any) {
      console.error('Error confirming rental:', err)
      alert(err.response?.data?.error || 'Error al confirmar el alquiler')
    } finally {
      setActionLoading(null)
    }
  }

  const handleCancel = async (alquiler: AlquilerMaquina) => {
    if (!confirm(`¿Cancelar el alquiler de ${alquiler.maquina_nombre} para el ${new Date(alquiler.fecha).toLocaleDateString('es-AR')}?`)) {
      return
    }

    setActionLoading(alquiler.id)
    try {
      await api.post(`/servicios/alquileres/${alquiler.id}/cancelar/`)
      await fetchAlquileres()
    } catch (err: any) {
      console.error('Error cancelling rental:', err)
      alert(err.response?.data?.error || 'Error al cancelar el alquiler')
    } finally {
      setActionLoading(null)
    }
  }

  const getEstadoBadge = (estado: EstadoAlquiler) => {
    const styles = {
      [EstadoAlquiler.PROGRAMADO]: 'bg-blue-100 text-blue-800',
      [EstadoAlquiler.CONFIRMADO]: 'bg-green-100 text-green-800',
      [EstadoAlquiler.CANCELADO]: 'bg-gray-100 text-gray-800',
      [EstadoAlquiler.COBRADO]: 'bg-purple-100 text-purple-800',
    }

    const icons = {
      [EstadoAlquiler.PROGRAMADO]: '📅',
      [EstadoAlquiler.CONFIRMADO]: '✓',
      [EstadoAlquiler.CANCELADO]: '✕',
      [EstadoAlquiler.COBRADO]: '💰',
    }

    return (
      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[estado]}`}>
        {icons[estado]} {estado}
      </span>
    )
  }

  const groupByMonth = (alquileres: AlquilerMaquina[]) => {
    const groups: { [key: string]: AlquilerMaquina[] } = {}

    alquileres.forEach(alquiler => {
      const date = new Date(alquiler.fecha)
      const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`

      if (!groups[key]) {
        groups[key] = []
      }
      groups[key].push(alquiler)
    })

    // Sort by date descending
    Object.keys(groups).forEach(key => {
      groups[key].sort((a, b) => new Date(b.fecha).getTime() - new Date(a.fecha).getTime())
    })

    return groups
  }

  const formatMonthYear = (key: string) => {
    const [year, month] = key.split('-')
    const date = new Date(parseInt(year), parseInt(month) - 1)
    return date.toLocaleDateString('es-AR', { month: 'long', year: 'numeric' })
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  const groupedAlquileres = groupByMonth(alquileres)

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900">Alquileres Programados</h3>
        <Button
          variant="primary"
          onClick={() => {
            setSelectedAlquiler(undefined)
            setShowForm(true)
          }}
        >
          + Programar Alquiler
        </Button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {alquileres.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
          <div className="text-4xl mb-3">📅</div>
          <h3 className="text-lg font-medium text-gray-900 mb-1">No hay alquileres programados</h3>
          <p className="text-gray-600 mb-4">Programa alquileres para controlar los gastos de máquinas</p>
          <Button
            variant="primary"
            onClick={() => setShowForm(true)}
          >
            Programar Primer Alquiler
          </Button>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.keys(groupedAlquileres).sort().reverse().map(monthKey => (
            <div key={monthKey}>
              <h4 className="text-sm font-semibold text-gray-700 uppercase mb-3">
                {formatMonthYear(monthKey)}
              </h4>
              <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Fecha
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Máquina
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Costo
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Estado
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Turnos
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Acciones
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {groupedAlquileres[monthKey].map(alquiler => (
                        <tr key={alquiler.id} className="hover:bg-gray-50 transition-colors">
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {new Date(alquiler.fecha).toLocaleDateString('es-AR', {
                              weekday: 'short',
                              day: '2-digit',
                              month: 'short',
                            })}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-gray-900">
                              {alquiler.maquina_nombre}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            ${alquiler.costo.toLocaleString('es-AR')}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            {getEstadoBadge(alquiler.estado)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            {alquiler.tiene_turnos ? (
                              <span className="text-green-600 font-medium">Con turnos</span>
                            ) : (
                              <span className="text-gray-400">Sin turnos</span>
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                            {alquiler.estado === EstadoAlquiler.PROGRAMADO && (
                              <>
                                <button
                                  onClick={() => handleConfirm(alquiler)}
                                  disabled={actionLoading === alquiler.id}
                                  className="text-green-600 hover:text-green-900 disabled:opacity-50"
                                  title="Confirmar alquiler"
                                >
                                  {actionLoading === alquiler.id ? '...' : '✓'}
                                </button>
                                <button
                                  onClick={() => handleEdit(alquiler)}
                                  className="text-blue-600 hover:text-blue-900"
                                  title="Editar alquiler"
                                >
                                  ✎
                                </button>
                                <button
                                  onClick={() => handleCancel(alquiler)}
                                  disabled={actionLoading === alquiler.id}
                                  className="text-red-600 hover:text-red-900 disabled:opacity-50"
                                  title="Cancelar alquiler"
                                >
                                  ✕
                                </button>
                              </>
                            )}

                            {alquiler.estado === EstadoAlquiler.CONFIRMADO && (
                              <>
                                <button
                                  onClick={() => handleEdit(alquiler)}
                                  className="text-blue-600 hover:text-blue-900"
                                  title="Editar alquiler"
                                >
                                  ✎
                                </button>
                                <button
                                  onClick={() => handleCancel(alquiler)}
                                  disabled={actionLoading === alquiler.id}
                                  className="text-red-600 hover:text-red-900 disabled:opacity-50"
                                  title="Cancelar alquiler"
                                >
                                  ✕
                                </button>
                              </>
                            )}

                            {alquiler.estado === EstadoAlquiler.COBRADO && (
                              <span className="text-purple-600 font-medium">
                                Transacción #{alquiler.transaccion_gasto}
                              </span>
                            )}

                            {alquiler.estado === EstadoAlquiler.CANCELADO && (
                              <span className="text-gray-400">Cancelado</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {showForm && (
        <AlquilerForm
          alquiler={selectedAlquiler}
          onSubmit={handleFormSubmit}
          onCancel={() => {
            setShowForm(false)
            setSelectedAlquiler(undefined)
          }}
        />
      )}
    </div>
  )
}

export default AlquileresList
