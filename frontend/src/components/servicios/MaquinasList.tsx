import { useEffect, useState } from 'react'
import { MaquinaAlquilada, PaginatedResponse } from '@/types/models'
import api from '@/services/api'
import toast from 'react-hot-toast'

interface MaquinasListProps {
  onEdit: (maquina: MaquinaAlquilada) => void
  refreshKey?: number
}

export default function MaquinasList({ onEdit, refreshKey = 0 }: MaquinasListProps) {
  const [maquinas, setMaquinas] = useState<MaquinaAlquilada[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchMaquinas()
  }, [refreshKey])

  const fetchMaquinas = async () => {
    setLoading(true)
    try {
      const response = await api.get<PaginatedResponse<MaquinaAlquilada>>('/servicios/maquinas/')
      // Check if response is paginated or direct array
      if (response.data && 'results' in response.data) {
        setMaquinas(response.data.results)
      } else {
        setMaquinas(response.data as any)
      }
    } catch (error) {
      console.error('Error loading machines:', error)
      toast.error('Error al cargar las máquinas')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('¿Estás seguro de eliminar esta máquina?')) {
      return
    }

    try {
      await api.delete(`/servicios/maquinas/${id}/`)
      toast.success('Máquina eliminada exitosamente')
      fetchMaquinas()
    } catch (error) {
      console.error('Error deleting machine:', error)
      toast.error('Error al eliminar la máquina')
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (maquinas.length === 0) {
    return (
      <div className="text-center py-12">
        <svg
          className="mx-auto h-12 w-12 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <h3 className="mt-2 text-sm font-medium text-gray-900">No hay máquinas alquiladas</h3>
        <p className="mt-1 text-sm text-gray-500">
          Comienza creando una nueva máquina para asociarla a tus servicios.
        </p>
      </div>
    )
  }

  return (
    <div className="bg-white shadow overflow-hidden sm:rounded-md">
      <ul className="divide-y divide-gray-200">
        {maquinas.map((maquina) => (
          <li key={maquina.id}>
            <div className="px-4 py-4 sm:px-6 hover:bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <p className="text-lg font-medium text-blue-600 truncate">
                      {maquina.nombre}
                    </p>
                    {!maquina.activa && (
                      <span className="ml-2 px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">
                        Inactiva
                      </span>
                    )}
                  </div>
                  {maquina.descripcion && (
                    <p className="mt-1 text-sm text-gray-600">{maquina.descripcion}</p>
                  )}
                  <div className="mt-2 flex items-center gap-4 text-sm text-gray-500">
                    <span className="flex items-center">
                      💰 <strong className="ml-1 text-green-600 text-base">
                        ${maquina.costo_diario.toLocaleString()}/día
                      </strong>
                    </span>
                    {maquina.proveedor && (
                      <span>
                        📦 {maquina.proveedor}
                      </span>
                    )}
                  </div>
                </div>
                <div className="ml-4 flex gap-2">
                  <button
                    onClick={() => onEdit(maquina)}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Editar
                  </button>
                  <button
                    onClick={() => handleDelete(maquina.id)}
                    className="inline-flex items-center px-3 py-2 border border-red-300 shadow-sm text-sm leading-4 font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                  >
                    Eliminar
                  </button>
                </div>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
