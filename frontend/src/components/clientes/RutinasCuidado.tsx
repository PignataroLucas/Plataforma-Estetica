import { useState, useEffect } from 'react'
import { RutinaCuidado } from '@/types/models'
import { getRutinasCuidado, createRutinaCuidado, updateRutinaCuidado, deleteRutinaCuidado } from '@/services/clienteService'
import { Button } from '@/components/ui'
import { formatDateArgentina } from '@/utils/dateUtils'

interface RutinasCuidadoProps {
  clienteId: number
}

export default function RutinasCuidado({ clienteId }: RutinasCuidadoProps) {
  const [rutinas, setRutinas] = useState<RutinaCuidado[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingRutina, setEditingRutina] = useState<RutinaCuidado | null>(null)
  const [formData, setFormData] = useState<Partial<RutinaCuidado>>({
    cliente: clienteId,
    rutina_diurna_pasos: '',
    rutina_diurna_productos: '',
    rutina_nocturna_pasos: '',
    rutina_nocturna_productos: '',
    activa: true,
  })

  useEffect(() => {
    loadRutinas()
  }, [clienteId])

  const loadRutinas = async () => {
    try {
      setLoading(true)
      const response = await getRutinasCuidado(clienteId)
      setRutinas(response.results)
    } catch (error) {
      console.error('Error loading routines:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    try {
      if (editingRutina) {
        await updateRutinaCuidado(editingRutina.id, formData)
      } else {
        await createRutinaCuidado(formData)
      }

      await loadRutinas()
      resetForm()
    } catch (error) {
      console.error('Error saving routine:', error)
      alert('Error al guardar la rutina')
    }
  }

  const handleEdit = (rutina: RutinaCuidado) => {
    setEditingRutina(rutina)
    setFormData({
      cliente: rutina.cliente,
      rutina_diurna_pasos: rutina.rutina_diurna_pasos,
      rutina_diurna_productos: rutina.rutina_diurna_productos,
      rutina_nocturna_pasos: rutina.rutina_nocturna_pasos,
      rutina_nocturna_productos: rutina.rutina_nocturna_productos,
      activa: rutina.activa,
    })
    setShowForm(true)
  }

  const handleDelete = async (id: number) => {
    if (!confirm('¿Estás seguro de eliminar esta rutina?')) return

    try {
      await deleteRutinaCuidado(id)
      await loadRutinas()
    } catch (error) {
      console.error('Error deleting routine:', error)
      alert('Error al eliminar la rutina')
    }
  }

  const handleToggleActive = async (rutina: RutinaCuidado) => {
    try {
      await updateRutinaCuidado(rutina.id, { activa: !rutina.activa })
      await loadRutinas()
    } catch (error) {
      console.error('Error updating routine:', error)
      alert('Error al actualizar la rutina')
    }
  }

  const resetForm = () => {
    setFormData({
      cliente: clienteId,
      rutina_diurna_pasos: '',
      rutina_diurna_productos: '',
      rutina_nocturna_pasos: '',
      rutina_nocturna_productos: '',
      activa: true,
    })
    setEditingRutina(null)
    setShowForm(false)
  }

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement | HTMLInputElement>) => {
    const { name, value, type } = e.target
    const checked = (e.target as HTMLInputElement).checked

    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
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
          Rutinas de Cuidado ({rutinas.length})
        </h3>
        <Button
          variant="primary"
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? 'Cancelar' : '+ Nueva Rutina'}
        </Button>
      </div>

      {/* Form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="bg-gray-50 p-4 rounded-lg space-y-6">
          {/* Rutina Diurna */}
          <div className="border-l-4 border-yellow-400 pl-4">
            <h4 className="font-semibold text-gray-900 mb-3">☀️ Rutina Diurna</h4>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Pasos
                </label>
                <textarea
                  name="rutina_diurna_pasos"
                  value={formData.rutina_diurna_pasos}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  rows={3}
                  placeholder="Ej: 1. Limpieza&#10;2. Tónico&#10;3. Serum&#10;4. Protector solar"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Productos Recomendados
                </label>
                <textarea
                  name="rutina_diurna_productos"
                  value={formData.rutina_diurna_productos}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  rows={3}
                  placeholder="Productos específicos para cada paso..."
                />
              </div>
            </div>
          </div>

          {/* Rutina Nocturna */}
          <div className="border-l-4 border-blue-400 pl-4">
            <h4 className="font-semibold text-gray-900 mb-3">🌙 Rutina Nocturna</h4>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Pasos
                </label>
                <textarea
                  name="rutina_nocturna_pasos"
                  value={formData.rutina_nocturna_pasos}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  rows={3}
                  placeholder="Ej: 1. Desmaquillante&#10;2. Limpieza&#10;3. Tónico&#10;4. Serum&#10;5. Crema de noche"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Productos Recomendados
                </label>
                <textarea
                  name="rutina_nocturna_productos"
                  value={formData.rutina_nocturna_productos}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  rows={3}
                  placeholder="Productos específicos para cada paso..."
                />
              </div>
            </div>
          </div>

          <div>
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                name="activa"
                checked={formData.activa}
                onChange={handleChange}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <span className="ml-2 text-sm text-gray-700 font-medium">
                Rutina Activa (mostrar como rutina actual)
              </span>
            </label>
          </div>

          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={resetForm}>
              Cancelar
            </Button>
            <Button type="submit" variant="primary">
              {editingRutina ? 'Actualizar Rutina' : 'Guardar Rutina'}
            </Button>
          </div>
        </form>
      )}

      {/* Routines List */}
      {rutinas.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-500">No hay rutinas de cuidado registradas</p>
          <p className="text-sm text-gray-400 mt-2">
            Haz clic en "Nueva Rutina" para agregar la primera rutina
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {rutinas.map((rutina) => (
            <div
              key={rutina.id}
              className={`border rounded-lg p-4 ${
                rutina.activa ? 'border-green-400 bg-green-50' : 'border-gray-200 bg-white'
              }`}
            >
              {/* Routine Header */}
              <div className="flex justify-between items-start mb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="font-semibold text-gray-900">
                      Rutina de Cuidado
                    </h4>
                    {rutina.activa && (
                      <span className="px-2 py-1 text-xs font-medium rounded bg-green-200 text-green-800">
                        ✓ Activa
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Creada el {formatDateArgentina(rutina.creado_en)} por {rutina.creado_por_nombre || 'Desconocido'}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleToggleActive(rutina)}
                    className="text-sm text-green-600 hover:text-green-800"
                  >
                    {rutina.activa ? 'Desactivar' : 'Activar'}
                  </button>
                  <button
                    onClick={() => handleEdit(rutina)}
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    Editar
                  </button>
                  <button
                    onClick={() => handleDelete(rutina.id)}
                    className="text-sm text-red-600 hover:text-red-800"
                  >
                    Eliminar
                  </button>
                </div>
              </div>

              {/* Routine Content */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Rutina Diurna */}
                <div className="border-l-4 border-yellow-400 pl-4">
                  <h5 className="font-medium text-gray-900 mb-2">☀️ Rutina Diurna</h5>
                  {rutina.rutina_diurna_pasos && (
                    <div className="mb-3">
                      <label className="text-xs font-medium text-gray-600">Pasos:</label>
                      <p className="text-sm text-gray-800 mt-1 whitespace-pre-wrap">
                        {rutina.rutina_diurna_pasos}
                      </p>
                    </div>
                  )}
                  {rutina.rutina_diurna_productos && (
                    <div>
                      <label className="text-xs font-medium text-gray-600">Productos:</label>
                      <p className="text-sm text-gray-800 mt-1 whitespace-pre-wrap">
                        {rutina.rutina_diurna_productos}
                      </p>
                    </div>
                  )}
                </div>

                {/* Rutina Nocturna */}
                <div className="border-l-4 border-blue-400 pl-4">
                  <h5 className="font-medium text-gray-900 mb-2">🌙 Rutina Nocturna</h5>
                  {rutina.rutina_nocturna_pasos && (
                    <div className="mb-3">
                      <label className="text-xs font-medium text-gray-600">Pasos:</label>
                      <p className="text-sm text-gray-800 mt-1 whitespace-pre-wrap">
                        {rutina.rutina_nocturna_pasos}
                      </p>
                    </div>
                  )}
                  {rutina.rutina_nocturna_productos && (
                    <div>
                      <label className="text-xs font-medium text-gray-600">Productos:</label>
                      <p className="text-sm text-gray-800 mt-1 whitespace-pre-wrap">
                        {rutina.rutina_nocturna_productos}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
