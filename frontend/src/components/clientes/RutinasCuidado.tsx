import { useState, useEffect } from 'react'
import type { MomentoRutina, RutinaCuidado, RutinaItem, ProductoList } from '@/types/models'
import { getRutinasCuidado, createRutinaCuidado, updateRutinaCuidado, deleteRutinaCuidado } from '@/services/clienteService'
import api from '@/services/api'
import { Button } from '@/components/ui'
import { formatDateArgentina } from '@/utils/dateUtils'

interface RutinasCuidadoProps {
  clienteId: number
}

interface FormState {
  cliente: number
  activa: boolean
  items: RutinaItem[]
}

const emptyForm = (clienteId: number): FormState => ({
  cliente: clienteId,
  activa: true,
  items: [],
})

const nuevoItem = (momento: MomentoRutina, orden: number): RutinaItem => ({
  momento,
  orden,
  paso: '',
  producto: null,
  producto_texto: '',
  nota: '',
})

export default function RutinasCuidado({ clienteId }: RutinasCuidadoProps) {
  const [rutinas, setRutinas] = useState<RutinaCuidado[]>([])
  const [productos, setProductos] = useState<ProductoList[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingRutina, setEditingRutina] = useState<RutinaCuidado | null>(null)
  const [formData, setFormData] = useState<FormState>(emptyForm(clienteId))

  useEffect(() => {
    loadRutinas()
    loadProductos()
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

  const loadProductos = async () => {
    try {
      // Sin page_size la API pagina de a 20 y el desplegable muestra solo los
      // primeros productos por orden alfabético. El catálogo entra cómodo en una
      // sola página; si algún día pasa de unos cientos, conviene agregar búsqueda
      // en vez de seguir subiendo este número (el backend topea page_size en 1000).
      const response = await api.get('/inventario/productos/', {
        params: { activo: true, page_size: 200 },
      })
      setProductos(response.data.results ?? response.data)
    } catch (error) {
      console.error('Error loading products:', error)
    }
  }

  // ---------- Manejo de items ----------

  const itemsDe = (momento: MomentoRutina) =>
    formData.items
      .map((item, index) => ({ item, index }))
      .filter((x) => x.item.momento === momento)

  const addItem = (momento: MomentoRutina) => {
    const orden = formData.items.filter((i) => i.momento === momento).length + 1
    setFormData((prev) => ({ ...prev, items: [...prev.items, nuevoItem(momento, orden)] }))
  }

  const updateItem = (index: number, patch: Partial<RutinaItem>) => {
    setFormData((prev) => ({
      ...prev,
      items: prev.items.map((it, i) => (i === index ? { ...it, ...patch } : it)),
    }))
  }

  const removeItem = (index: number) => {
    setFormData((prev) => ({ ...prev, items: prev.items.filter((_, i) => i !== index) }))
  }

  // ---------- Submit ----------

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    // Descarta filas vacías y recalcula el orden dentro de cada momento.
    const preparar = (momento: MomentoRutina) =>
      formData.items
        .filter((i) => i.momento === momento)
        .filter((i) => i.paso.trim() || i.producto || (i.producto_texto ?? '').trim())
        .map((i, idx) => ({ ...i, orden: idx + 1 }))

    const payload = {
      cliente: formData.cliente,
      activa: formData.activa,
      items: [...preparar('DIURNA'), ...preparar('NOCTURNA')],
    }

    try {
      if (editingRutina) {
        await updateRutinaCuidado(editingRutina.id, payload)
      } else {
        await createRutinaCuidado(payload)
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
      activa: rutina.activa,
      items: (rutina.items ?? []).map((it) => ({
        momento: it.momento,
        orden: it.orden,
        paso: it.paso ?? '',
        producto: it.producto ?? null,
        producto_texto: it.producto_texto ?? '',
        nota: it.nota ?? '',
      })),
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
    setFormData(emptyForm(clienteId))
    setEditingRutina(null)
    setShowForm(false)
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  const productoNombre = (id?: number | null) => {
    if (!id) return null
    const p = productos.find((x) => x.id === id)
    return p ? p.nombre : `Producto #${id}`
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900">
          Rutinas de Cuidado ({rutinas.length})
        </h3>
        <Button variant="primary" onClick={() => (showForm ? resetForm() : setShowForm(true))}>
          {showForm ? 'Cancelar' : '+ Nueva Rutina'}
        </Button>
      </div>

      {/* Form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="bg-gray-50 p-4 rounded-lg space-y-6">
          {(['DIURNA', 'NOCTURNA'] as MomentoRutina[]).map((momento) => {
            const esDia = momento === 'DIURNA'
            const items = itemsDe(momento)
            return (
              <div
                key={momento}
                className={`border-l-4 pl-4 ${esDia ? 'border-yellow-400' : 'border-blue-400'}`}
              >
                <h4 className="font-semibold text-gray-900 mb-3">
                  {esDia ? '☀️ Rutina Diurna' : '🌙 Rutina Nocturna'}
                </h4>

                <div className="space-y-3">
                  {items.length === 0 && (
                    <p className="text-sm text-gray-400">Sin pasos todavía.</p>
                  )}

                  {items.map(({ item, index }, pos) => (
                    <div key={index} className="bg-white border border-gray-200 rounded-lg p-3 space-y-2">
                      <div className="flex items-start gap-2">
                        <span className="mt-2 text-xs font-medium text-gray-400 w-5">{pos + 1}.</span>
                        <input
                          type="text"
                          value={item.paso}
                          onChange={(e) => updateItem(index, { paso: e.target.value })}
                          placeholder="Paso (ej: Limpieza, Serum, Protector solar)"
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                        />
                        <button
                          type="button"
                          onClick={() => removeItem(index)}
                          className="mt-1 text-gray-400 hover:text-red-600 text-lg leading-none px-1"
                          aria-label="Eliminar paso"
                        >
                          ×
                        </button>
                      </div>

                      <div className="flex gap-2 pl-7">
                        <select
                          value={item.producto ?? ''}
                          onChange={(e) =>
                            updateItem(index, { producto: e.target.value ? Number(e.target.value) : null })
                          }
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                        >
                          <option value="">— Producto del catálogo (opcional) —</option>
                          {productos.map((p) => (
                            <option key={p.id} value={p.id}>
                              {p.nombre}{p.marca ? ` · ${p.marca}` : ''}
                            </option>
                          ))}
                        </select>
                        <input
                          type="text"
                          value={item.producto_texto ?? ''}
                          onChange={(e) => updateItem(index, { producto_texto: e.target.value })}
                          placeholder="o producto libre"
                          className="w-40 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                        />
                      </div>

                      <div className="pl-7">
                        <input
                          type="text"
                          value={item.nota ?? ''}
                          onChange={(e) => updateItem(index, { nota: e.target.value })}
                          placeholder="Indicación (opcional, ej: aplicar en rostro y cuello)"
                          className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                        />
                      </div>
                    </div>
                  ))}

                  <button
                    type="button"
                    onClick={() => addItem(momento)}
                    className="text-sm text-primary-600 hover:text-primary-800 font-medium"
                  >
                    + Agregar paso
                  </button>
                </div>
              </div>
            )
          })}

          <div>
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={formData.activa}
                onChange={(e) => setFormData((prev) => ({ ...prev, activa: e.target.checked }))}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <span className="ml-2 text-sm text-gray-700 font-medium">
                Rutina Activa (es la que ve el cliente en la app)
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
            Hacé clic en &quot;Nueva Rutina&quot; para agregar la primera rutina
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
                    <h4 className="font-semibold text-gray-900">Rutina de Cuidado</h4>
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
                  <button onClick={() => handleToggleActive(rutina)} className="text-sm text-green-600 hover:text-green-800">
                    {rutina.activa ? 'Desactivar' : 'Activar'}
                  </button>
                  <button onClick={() => handleEdit(rutina)} className="text-sm text-blue-600 hover:text-blue-800">
                    Editar
                  </button>
                  <button onClick={() => handleDelete(rutina.id)} className="text-sm text-red-600 hover:text-red-800">
                    Eliminar
                  </button>
                </div>
              </div>

              {/* Routine Content */}
              {rutina.items && rutina.items.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {(['DIURNA', 'NOCTURNA'] as MomentoRutina[]).map((momento) => {
                    const esDia = momento === 'DIURNA'
                    const items = (rutina.items ?? []).filter((i) => i.momento === momento)
                    if (items.length === 0) return null
                    return (
                      <div key={momento} className={`border-l-4 pl-4 ${esDia ? 'border-yellow-400' : 'border-blue-400'}`}>
                        <h5 className="font-medium text-gray-900 mb-2">
                          {esDia ? '☀️ Rutina Diurna' : '🌙 Rutina Nocturna'}
                        </h5>
                        <ol className="space-y-2">
                          {items.map((item, i) => (
                            <li key={item.id ?? i} className="text-sm text-gray-800">
                              <span className="font-medium">{i + 1}. {item.paso}</span>
                              {(item.producto || item.producto_texto) && (
                                <span className="block text-xs text-gray-500 ml-4">
                                  🏷️ {item.producto_nombre || productoNombre(item.producto) || item.producto_texto}
                                </span>
                              )}
                              {item.nota && (
                                <span className="block text-xs text-gray-400 ml-4">{item.nota}</span>
                              )}
                            </li>
                          ))}
                        </ol>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <RutinaLegacy rutina={rutina} />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

/** Compatibilidad: rutinas viejas guardadas como texto libre (sin items). */
function RutinaLegacy({ rutina }: { rutina: RutinaCuidado }) {
  const bloques = [
    { titulo: '☀️ Rutina Diurna', color: 'border-yellow-400', pasos: rutina.rutina_diurna_pasos, productos: rutina.rutina_diurna_productos },
    { titulo: '🌙 Rutina Nocturna', color: 'border-blue-400', pasos: rutina.rutina_nocturna_pasos, productos: rutina.rutina_nocturna_productos },
  ].filter((b) => b.pasos || b.productos)

  if (bloques.length === 0) {
    return <p className="text-sm text-gray-400">Sin pasos cargados.</p>
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {bloques.map((b) => (
        <div key={b.titulo} className={`border-l-4 pl-4 ${b.color}`}>
          <h5 className="font-medium text-gray-900 mb-2">{b.titulo}</h5>
          {b.pasos && (
            <p className="text-sm text-gray-800 whitespace-pre-wrap">{b.pasos}</p>
          )}
          {b.productos && (
            <p className="text-sm text-gray-600 mt-2 whitespace-pre-wrap">{b.productos}</p>
          )}
        </div>
      ))}
    </div>
  )
}
