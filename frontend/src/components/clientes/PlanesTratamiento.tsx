import { useState, useEffect } from 'react'
import { PlanTratamiento } from '@/types/models'
import { getPlanesTratamiento, createPlanTratamiento, updatePlanTratamiento, deletePlanTratamiento } from '@/services/clienteService'
import { Button, Input, DateInput } from '@/components/ui'
import { formatDateArgentina } from '@/utils/dateUtils'

interface PlanesTratamientoProps {
  clienteId: number
}

export default function PlanesTratamiento({ clienteId }: PlanesTratamientoProps) {
  const [planes, setPlanes] = useState<PlanTratamiento[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingPlan, setEditingPlan] = useState<PlanTratamiento | null>(null)
  const [formData, setFormData] = useState<Partial<PlanTratamiento>>({
    cliente: clienteId,
    tratamiento_sugerido: '',
    frecuencia: '',
    sesiones_estimadas: undefined,
    indicaciones: '',
    proximo_turno: '',
  })

  useEffect(() => {
    loadPlanes()
  }, [clienteId])

  const loadPlanes = async () => {
    try {
      setLoading(true)
      const response = await getPlanesTratamiento(clienteId)
      setPlanes(response.results)
    } catch (error) {
      console.error('Error loading treatment plans:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    try {
      if (editingPlan) {
        await updatePlanTratamiento(editingPlan.id, formData)
      } else {
        await createPlanTratamiento(formData)
      }

      await loadPlanes()
      resetForm()
    } catch (error) {
      console.error('Error saving treatment plan:', error)
      alert('Error al guardar el plan de tratamiento')
    }
  }

  const handleEdit = (plan: PlanTratamiento) => {
    setEditingPlan(plan)
    setFormData({
      cliente: plan.cliente,
      tratamiento_sugerido: plan.tratamiento_sugerido,
      frecuencia: plan.frecuencia,
      sesiones_estimadas: plan.sesiones_estimadas,
      indicaciones: plan.indicaciones,
      proximo_turno: plan.proximo_turno,
    })
    setShowForm(true)
  }

  const handleDelete = async (id: number) => {
    if (!confirm('¿Estás seguro de eliminar este plan de tratamiento?')) return

    try {
      await deletePlanTratamiento(id)
      await loadPlanes()
    } catch (error) {
      console.error('Error deleting treatment plan:', error)
      alert('Error al eliminar el plan')
    }
  }

  const resetForm = () => {
    setFormData({
      cliente: clienteId,
      tratamiento_sugerido: '',
      frecuencia: '',
      sesiones_estimadas: undefined,
      indicaciones: '',
      proximo_turno: '',
    })
    setEditingPlan(null)
    setShowForm(false)
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target

    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? (value ? parseInt(value) : undefined) : value,
    }))
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900">
          Planes de Tratamiento ({planes.length})
        </h3>
        <Button
          variant="primary"
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? 'Cancelar' : '+ Nuevo Plan'}
        </Button>
      </div>

      {/* Form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="bg-gray-50 p-4 rounded-lg space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tratamiento Sugerido *
            </label>
            <textarea
              name="tratamiento_sugerido"
              value={formData.tratamiento_sugerido}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              rows={3}
              placeholder="Descripción del tratamiento sugerido..."
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Input
              label="Frecuencia"
              name="frecuencia"
              value={formData.frecuencia}
              onChange={handleChange}
              placeholder="Ej: Semanal"
              fullWidth
            />

            <Input
              label="Sesiones Estimadas"
              type="number"
              name="sesiones_estimadas"
              value={formData.sesiones_estimadas || ''}
              onChange={handleChange}
              placeholder="Número"
              fullWidth
            />

            <DateInput
              label="Próximo Turno"
              value={formData.proximo_turno || ''}
              onChange={(value) => setFormData(prev => ({ ...prev, proximo_turno: value }))}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Indicaciones / Homecare / Post Tratamiento
            </label>
            <textarea
              name="indicaciones"
              value={formData.indicaciones}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              rows={3}
              placeholder="Indicaciones y cuidados..."
            />
          </div>

          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={resetForm}>
              Cancelar
            </Button>
            <Button type="submit" variant="primary">
              {editingPlan ? 'Actualizar Plan' : 'Guardar Plan'}
            </Button>
          </div>
        </form>
      )}

      {/* Plans List */}
      {planes.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-500">No hay planes de tratamiento registrados</p>
          <p className="text-sm text-gray-400 mt-2">
            Haz clic en "Nuevo Plan" para agregar el primer plan
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {planes.map((plan) => (
            <div
              key={plan.id}
              className="border border-gray-200 rounded-lg p-4 bg-white hover:shadow-md transition-shadow"
            >
              {/* Plan Header */}
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h4 className="font-semibold text-gray-900">
                    Plan de Tratamiento
                  </h4>
                  <p className="text-xs text-gray-500 mt-1">
                    Creado el {formatDateArgentina(plan.creado_en)} por {plan.creado_por_nombre || 'Desconocido'}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleEdit(plan)}
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    Editar
                  </button>
                  <button
                    onClick={() => handleDelete(plan.id)}
                    className="text-sm text-red-600 hover:text-red-800"
                  >
                    Eliminar
                  </button>
                </div>
              </div>

              {/* Plan Content */}
              <div className="space-y-3">
                <div>
                  <label className="text-sm font-medium text-gray-700">Tratamiento:</label>
                  <p className="text-gray-800 mt-1 whitespace-pre-wrap">{plan.tratamiento_sugerido}</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {plan.frecuencia && (
                    <div>
                      <label className="text-sm font-medium text-gray-700">Frecuencia:</label>
                      <p className="text-gray-800">{plan.frecuencia}</p>
                    </div>
                  )}
                  {plan.sesiones_estimadas && (
                    <div>
                      <label className="text-sm font-medium text-gray-700">Sesiones:</label>
                      <p className="text-gray-800">{plan.sesiones_estimadas}</p>
                    </div>
                  )}
                  {plan.proximo_turno && (
                    <div>
                      <label className="text-sm font-medium text-gray-700">Próximo Turno:</label>
                      <p className="text-gray-800">{formatDateArgentina(plan.proximo_turno)}</p>
                    </div>
                  )}
                </div>

                {plan.indicaciones && (
                  <div>
                    <label className="text-sm font-medium text-gray-700">Indicaciones:</label>
                    <p className="text-gray-800 mt-1 whitespace-pre-wrap">{plan.indicaciones}</p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
