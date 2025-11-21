import { useState, useEffect } from 'react'
import { AlquilerMaquina, EstadoAlquiler, MaquinaAlquilada, PaginatedResponse } from '@/types/models'
import api from '@/services/api'
import { Input, Select, Button } from '@/components/ui'

interface AlquilerFormProps {
  alquiler?: AlquilerMaquina
  maquinaId?: number
  onSubmit: (alquiler: AlquilerMaquina) => void
  onCancel: () => void
}

const AlquilerForm = ({ alquiler, maquinaId, onSubmit, onCancel }: AlquilerFormProps) => {
  const [formData, setFormData] = useState({
    maquina: maquinaId?.toString() || '',
    fecha: '',
    estado: EstadoAlquiler.PROGRAMADO,
    costo: '',
    notas: '',
  })

  const [maquinas, setMaquinas] = useState<MaquinaAlquilada[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [costoAutomatico, setCostoAutomatico] = useState(true)

  useEffect(() => {
    fetchMaquinas()
  }, [])

  useEffect(() => {
    if (alquiler) {
      setFormData({
        maquina: alquiler.maquina.toString(),
        fecha: alquiler.fecha,
        estado: alquiler.estado,
        costo: alquiler.costo.toString(),
        notas: alquiler.notas || '',
      })
      setCostoAutomatico(false)
    }
  }, [alquiler])

  // Auto-fill costo when machine is selected
  useEffect(() => {
    if (formData.maquina && costoAutomatico) {
      const maquina = maquinas.find(m => m.id === parseInt(formData.maquina))
      if (maquina) {
        setFormData(prev => ({ ...prev, costo: maquina.costo_diario.toString() }))
      }
    }
  }, [formData.maquina, maquinas, costoAutomatico])

  const fetchMaquinas = async () => {
    try {
      const response = await api.get<PaginatedResponse<MaquinaAlquilada>>('/servicios/maquinas/')
      const maquinasList = response.data && 'results' in response.data
        ? response.data.results
        : response.data as any
      setMaquinas(maquinasList.filter((m: MaquinaAlquilada) => m.activa))
    } catch (err) {
      console.error('Error loading machines:', err)
      setError('Error al cargar las máquinas')
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))

    // If user manually changes cost, disable auto-fill
    if (name === 'costo') {
      setCostoAutomatico(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const payload = {
        maquina: parseInt(formData.maquina),
        fecha: formData.fecha,
        estado: formData.estado,
        costo: parseFloat(formData.costo),
        notas: formData.notas,
      }

      let response
      if (alquiler) {
        response = await api.patch<AlquilerMaquina>(`/servicios/alquileres/${alquiler.id}/`, payload)
      } else {
        response = await api.post<AlquilerMaquina>('/servicios/alquileres/', payload)
      }

      onSubmit(response.data)
    } catch (err: any) {
      console.error('Error saving rental:', err)
      if (err.response?.data) {
        const errors = err.response.data
        if (typeof errors === 'object') {
          const firstError = Object.values(errors)[0]
          setError(Array.isArray(firstError) ? firstError[0] : String(firstError))
        } else {
          setError('Error al guardar el alquiler')
        }
      } else {
        setError('Error al guardar el alquiler')
      }
    } finally {
      setLoading(false)
    }
  }

  const maquinaNombre = formData.maquina
    ? maquinas.find(m => m.id === parseInt(formData.maquina))?.nombre
    : ''

  // Prepare options for Select components
  const maquinasOptions = [
    { value: '', label: 'Seleccionar máquina...', disabled: true },
    ...maquinas.map(m => ({
      value: m.id.toString(),
      label: `${m.nombre} - $${m.costo_diario.toLocaleString('es-AR')}/día`
    }))
  ]

  const estadoOptions = [
    { value: EstadoAlquiler.PROGRAMADO, label: 'Programado' },
    { value: EstadoAlquiler.CONFIRMADO, label: 'Confirmado' },
    ...(alquiler ? [
      { value: EstadoAlquiler.CANCELADO, label: 'Cancelado' },
      { value: EstadoAlquiler.COBRADO, label: 'Cobrado' }
    ] : [])
  ]

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center">
          <h2 className="text-xl font-semibold text-gray-900">
            {alquiler ? 'Editar Alquiler' : 'Programar Alquiler'}
          </h2>
          <button
            onClick={onCancel}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          <Select
            label="Máquina"
            name="maquina"
            value={formData.maquina}
            onChange={handleChange}
            options={maquinasOptions}
            placeholder="Seleccionar máquina..."
            required
            disabled={!!maquinaId || !!alquiler}
            fullWidth
          />

          <Input
            label="Fecha"
            type="date"
            name="fecha"
            value={formData.fecha}
            onChange={handleChange}
            required
            min={new Date().toISOString().split('T')[0]}
          />

          <Select
            label="Estado"
            name="estado"
            value={formData.estado}
            onChange={handleChange}
            options={estadoOptions}
            placeholder="Seleccionar estado..."
            required
            fullWidth
          />

          {formData.estado === EstadoAlquiler.PROGRAMADO && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm">
              <p className="font-medium text-blue-900">Estado: Programado</p>
              <p className="text-blue-700 mt-1">
                El alquiler está programado pero no confirmado. No se creará gasto automáticamente.
              </p>
            </div>
          )}

          {formData.estado === EstadoAlquiler.CONFIRMADO && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-sm">
              <p className="font-medium text-green-900">Estado: Confirmado</p>
              <p className="text-green-700 mt-1">
                Al completar un turno con {maquinaNombre} en esta fecha, se creará automáticamente un gasto de ${formData.costo ? parseFloat(formData.costo).toLocaleString('es-AR') : '0'} en Finanzas.
              </p>
            </div>
          )}

          {formData.estado === EstadoAlquiler.COBRADO && (
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-3 text-sm">
              <p className="font-medium text-purple-900">Estado: Cobrado</p>
              <p className="text-purple-700 mt-1">
                Este alquiler ya generó una transacción de gasto en Finanzas y no se puede modificar.
              </p>
            </div>
          )}

          <Input
            label="Costo"
            type="number"
            name="costo"
            value={formData.costo}
            onChange={handleChange}
            required
            min="0"
            step="0.01"
            placeholder="0.00"
            helpText={costoAutomatico ? 'Costo automático según la máquina seleccionada' : 'Costo personalizado'}
          />

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Notas
            </label>
            <textarea
              name="notas"
              value={formData.notas}
              onChange={handleChange}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
              placeholder="Notas adicionales sobre el alquiler..."
            />
          </div>

          <div className="flex gap-3 pt-4">
            <Button
              type="button"
              variant="secondary"
              onClick={onCancel}
              disabled={loading}
              className="flex-1"
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              variant="primary"
              loading={loading}
              className="flex-1"
            >
              {alquiler ? 'Actualizar' : 'Programar'} Alquiler
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default AlquilerForm
