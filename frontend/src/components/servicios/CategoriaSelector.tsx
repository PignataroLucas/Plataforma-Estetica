import { useEffect, useState, KeyboardEvent } from 'react'
import toast from 'react-hot-toast'
import { CategoriaServicio, PaginatedResponse } from '@/types/models'
import { Button } from '@/components/ui'
import api from '@/services/api'

/**
 * CategoriaSelector - Elige (o crea al vuelo) la categoría de un servicio.
 *
 * Las categorías son las que la app del cliente muestra en "Categorías" de
 * Inicio y como filtros del catálogo. Un servicio sin categoría no aparece en
 * ninguna, y si ningún servicio tiene, la sección directamente no se muestra.
 */

const NUEVA = '__nueva__'

interface CategoriaSelectorProps {
  value: number | null
  onChange: (categoria: number | null) => void
}

export default function CategoriaSelector({ value, onChange }: CategoriaSelectorProps) {
  const [categorias, setCategorias] = useState<CategoriaServicio[]>([])
  const [loading, setLoading] = useState(false)
  const [creando, setCreando] = useState(false)
  const [nombreNueva, setNombreNueva] = useState('')
  const [guardando, setGuardando] = useState(false)

  useEffect(() => {
    const fetchCategorias = async () => {
      setLoading(true)
      try {
        const response = await api.get<PaginatedResponse<CategoriaServicio>>('/servicios/categorias/')
        const lista = response.data && 'results' in response.data
          ? response.data.results
          : response.data as any
        setCategorias(lista)
      } catch (error) {
        console.error('Error loading categories:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchCategorias()
  }, [])

  // Las inactivas no se ofrecen, salvo la que el servicio ya tiene: si no, el
  // select quedaría en blanco y parecería que no tiene categoría.
  const visibles = categorias.filter(c => c.activa || c.id === value)

  const handleSelect = (seleccion: string) => {
    if (seleccion === NUEVA) {
      setCreando(true)
      return
    }
    onChange(seleccion ? parseInt(seleccion) : null)
  }

  const cancelarNueva = () => {
    setCreando(false)
    setNombreNueva('')
  }

  const crearCategoria = async () => {
    const nombre = nombreNueva.trim()
    if (!nombre) return

    setGuardando(true)
    try {
      const response = await api.post<CategoriaServicio>('/servicios/categorias/', { nombre })
      setCategorias(prev =>
        [...prev, response.data].sort((a, b) => a.nombre.localeCompare(b.nombre, 'es'))
      )
      onChange(response.data.id)
      cancelarNueva()
      toast.success(`Categoría "${response.data.nombre}" creada`)
    } catch (err: any) {
      toast.error(err.response?.data?.nombre?.[0] || 'Error al crear la categoría')
    } finally {
      setGuardando(false)
    }
  }

  // El selector vive dentro del <form> del servicio: Enter acá crearía el
  // servicio en vez de la categoría.
  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      crearCategoria()
    } else if (e.key === 'Escape') {
      e.preventDefault()
      cancelarNueva()
    }
  }

  return (
    <div>
      <label htmlFor="categoria" className="block text-sm font-medium text-gray-700 mb-1">
        Categoría
      </label>

      {creando ? (
        <div className="flex gap-2">
          <input
            id="categoria"
            type="text"
            value={nombreNueva}
            onChange={e => setNombreNueva(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ej: Facial, Corporal"
            maxLength={100}
            autoFocus
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <Button
            type="button"
            variant="primary"
            onClick={crearCategoria}
            loading={guardando}
            disabled={!nombreNueva.trim()}
          >
            Crear
          </Button>
          <Button type="button" variant="secondary" onClick={cancelarNueva} disabled={guardando}>
            Cancelar
          </Button>
        </div>
      ) : (
        <select
          id="categoria"
          name="categoria"
          value={value ?? ''}
          onChange={e => handleSelect(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={loading}
        >
          <option value="">Sin categoría</option>
          {visibles.map(categoria => (
            <option key={categoria.id} value={categoria.id}>
              {categoria.nombre}
              {!categoria.activa ? ' (inactiva)' : ''}
            </option>
          ))}
          <option value={NUEVA}>+ Nueva categoría…</option>
        </select>
      )}

      <p className="mt-1 text-xs text-gray-500">
        Agrupa el tratamiento en la app del cliente (Inicio y catálogo). Sin categoría, no
        aparece en ninguna.
      </p>
    </div>
  )
}
