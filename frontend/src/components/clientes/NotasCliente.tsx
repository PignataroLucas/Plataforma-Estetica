import { useState, useEffect } from 'react'
import { NotaCliente, TipoNota, VisibilidadNota } from '@/types/models'
import { getNotasCliente, createNotaCliente, updateNotaCliente, deleteNotaCliente } from '@/services/clienteService'
import { Button, Select } from '@/components/ui'
import { formatDateArgentina } from '@/utils/dateUtils'

interface NotasClienteProps {
  clienteId: number
}

const tipoNotaOptions = [
  { value: 'GENERAL', label: 'General' },
  { value: 'RECORDATORIO', label: 'Recordatorio' },
  { value: 'OBSERVACION', label: 'Observación' },
  { value: 'IMPORTANTE', label: 'Importante' },
  { value: 'SEGUIMIENTO', label: 'Seguimiento' },
]

const visibilidadOptions = [
  { value: 'TODOS', label: 'Todos' },
  { value: 'SOLO_ADMIN', label: 'Solo Admin' },
  { value: 'SOLO_AUTOR', label: 'Solo Autor' },
]

const tipoNotaColors: Record<TipoNota, string> = {
  GENERAL: 'bg-gray-100 text-gray-800',
  RECORDATORIO: 'bg-blue-100 text-blue-800',
  OBSERVACION: 'bg-purple-100 text-purple-800',
  IMPORTANTE: 'bg-red-100 text-red-800',
  SEGUIMIENTO: 'bg-green-100 text-green-800',
}

export default function NotasCliente({ clienteId }: NotasClienteProps) {
  const [notas, setNotas] = useState<NotaCliente[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingNota, setEditingNota] = useState<NotaCliente | null>(null)
  const [formData, setFormData] = useState<Partial<NotaCliente>>({
    cliente: clienteId,
    tipo_nota: 'GENERAL' as TipoNota,
    contenido: '',
    visible_para: 'TODOS' as VisibilidadNota,
    destacada: false,
  })

  useEffect(() => {
    loadNotas()
  }, [clienteId])

  const loadNotas = async () => {
    try {
      setLoading(true)
      const response = await getNotasCliente(clienteId)
      setNotas(response.results)
    } catch (error) {
      console.error('Error loading notes:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    try {
      if (editingNota) {
        await updateNotaCliente(editingNota.id, formData)
      } else {
        await createNotaCliente(formData)
      }

      await loadNotas()
      resetForm()
    } catch (error) {
      console.error('Error saving note:', error)
      alert('Error al guardar la nota')
    }
  }

  const handleEdit = (nota: NotaCliente) => {
    setEditingNota(nota)
    setFormData({
      cliente: nota.cliente,
      tipo_nota: nota.tipo_nota,
      contenido: nota.contenido,
      visible_para: nota.visible_para,
      destacada: nota.destacada,
    })
    setShowForm(true)
  }

  const handleDelete = async (id: number) => {
    if (!confirm('¿Estás seguro de eliminar esta nota?')) return

    try {
      await deleteNotaCliente(id)
      await loadNotas()
    } catch (error) {
      console.error('Error deleting note:', error)
      alert('Error al eliminar la nota')
    }
  }

  const resetForm = () => {
    setFormData({
      cliente: clienteId,
      tipo_nota: 'GENERAL' as TipoNota,
      contenido: '',
      visible_para: 'TODOS' as VisibilidadNota,
      destacada: false,
    })
    setEditingNota(null)
    setShowForm(false)
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
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
          Notas del Paciente ({notas.length})
        </h3>
        <Button
          variant="primary"
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? 'Cancelar' : '+ Nueva Nota'}
        </Button>
      </div>

      {/* Form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="bg-gray-50 p-4 rounded-lg space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Select
              label="Tipo de Nota"
              name="tipo_nota"
              value={formData.tipo_nota}
              onChange={handleChange}
              options={tipoNotaOptions}
              required
            />

            <Select
              label="Visible Para"
              name="visible_para"
              value={formData.visible_para}
              onChange={handleChange}
              options={visibilidadOptions}
              required
            />

            <div className="flex items-center">
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  name="destacada"
                  checked={formData.destacada}
                  onChange={handleChange}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700 font-medium">
                  Nota Destacada
                </span>
              </label>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Contenido de la Nota *
            </label>
            <textarea
              name="contenido"
              value={formData.contenido}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              rows={4}
              placeholder="Escribe el contenido de la nota..."
            />
          </div>

          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={resetForm}>
              Cancelar
            </Button>
            <Button type="submit" variant="primary">
              {editingNota ? 'Actualizar Nota' : 'Guardar Nota'}
            </Button>
          </div>
        </form>
      )}

      {/* Notes List */}
      {notas.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-500">No hay notas registradas para este paciente</p>
          <p className="text-sm text-gray-400 mt-2">
            Haz clic en "Nueva Nota" para agregar la primera nota
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {notas.map((nota) => (
            <div
              key={nota.id}
              className={`border rounded-lg p-4 ${
                nota.destacada ? 'border-yellow-400 bg-yellow-50' : 'border-gray-200 bg-white'
              }`}
            >
              {/* Note Header */}
              <div className="flex justify-between items-start mb-3">
                <div className="flex items-center gap-2">
                  <span
                    className={`px-2 py-1 text-xs font-medium rounded ${
                      tipoNotaColors[nota.tipo_nota]
                    }`}
                  >
                    {tipoNotaOptions.find((t) => t.value === nota.tipo_nota)?.label}
                  </span>
                  {nota.destacada && (
                    <span className="px-2 py-1 text-xs font-medium rounded bg-yellow-200 text-yellow-800">
                      ★ Destacada
                    </span>
                  )}
                  <span className="text-xs text-gray-500">
                    {visibilidadOptions.find((v) => v.value === nota.visible_para)?.label}
                  </span>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleEdit(nota)}
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    Editar
                  </button>
                  <button
                    onClick={() => handleDelete(nota.id)}
                    className="text-sm text-red-600 hover:text-red-800"
                  >
                    Eliminar
                  </button>
                </div>
              </div>

              {/* Note Content */}
              <p className="text-gray-800 whitespace-pre-wrap mb-3">{nota.contenido}</p>

              {/* Note Footer */}
              <div className="flex justify-between items-center text-xs text-gray-500 pt-3 border-t border-gray-200">
                <span>
                  Por: <span className="font-medium">{nota.autor_nombre || 'Desconocido'}</span>
                </span>
                <span>{formatDateArgentina(nota.creado_en)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
