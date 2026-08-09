import { useState } from 'react'
import api from '../services/api'
import type { Producto, ProductoFormData, ProductoList, ProductoDetail, TipoMovimiento } from '../types/models'

interface UseProductosReturn {
  productos: ProductoList[]
  loading: boolean
  error: string | null
  fetchProductos: (params?: FetchProductosParams) => Promise<void>
  fetchProducto: (id: number) => Promise<ProductoDetail | null>
  createProducto: (data: ProductoFormData) => Promise<Producto | null>
  updateProducto: (id: number, data: ProductoFormData) => Promise<Producto | null>
  deleteProducto: (id: number) => Promise<boolean>
  ajustarStock: (id: number, data: AjustarStockData) => Promise<boolean>
  fetchStockBajo: () => Promise<ProductoList[]>
  clearError: () => void
}

interface FetchProductosParams {
  tipo?: string
  categoria?: number
  proveedor?: number
  activo?: boolean
  search?: string
}

interface AjustarStockData {
  tipo_movimiento: TipoMovimiento
  cantidad: number
  motivo?: string
  notas?: string
  costo_unitario?: number
}

/**
 * Campos de los que manda Conto.
 *
 * El sync los actualiza por su cuenta con un UPDATE acotado. Como el CRM guarda
 * con PUT mandando el formulario entero, si viajaran alcanzaría con tener el
 * formulario abierto un rato: se abre a las 10:00, el sync corre a las 10:05 y
 * el guardado de las 10:10 reescribe stock y precios con los valores viejos.
 * Es silencioso y dura hasta el próximo sync.
 *
 * Se omiten al editar, no al crear: un producto nuevo necesita costo y precio.
 */
const CAMPOS_DE_CONTO = ['stock_actual', 'precio_costo', 'precio_venta']

/**
 * Campos que llegan en initialData pero son de solo lectura en la API: si
 * viajan, el serializer los ignora o se queja.
 */
const CAMPOS_DE_SOLO_LECTURA = [
  'id', 'sucursal', 'foto_thumb', 'creado_en', 'actualizado_en',
  'margen_ganancia', 'stock_bajo', 'categoria_nombre', 'proveedor_nombre',
  'categoria_data', 'proveedor_data',
]

/**
 * Campos que el backend no acepta en blanco: una FK, un decimal opcional o un
 * código único mandados como '' son un error de validación.
 */
const OMITIR_SI_ESTAN_VACIOS = [
  'categoria', 'proveedor', 'codigo_barras', 'stock_maximo',
  'precio_efectivo', 'precio_transferencia', 'precio_debito', 'precio_credito',
]

/**
 * Arma el cuerpo del request. Devuelve un FormData si hay que mover un archivo
 * y un objeto plano (JSON) si no, que es el caso de la enorme mayoría de los
 * guardados.
 */
export const prepararPayload = (data: ProductoFormData, esEdicion: boolean) => {
  const campos: Record<string, any> = { ...data }

  CAMPOS_DE_SOLO_LECTURA.forEach(campo => delete campos[campo])
  if (esEdicion) {
    CAMPOS_DE_CONTO.forEach(campo => delete campos[campo])
  }

  Object.keys(campos).forEach(campo => {
    const valor = campos[campo]
    if (valor === undefined || valor === null) {
      delete campos[campo]
    } else if (valor === '' && OMITIR_SI_ESTAN_VACIOS.includes(campo)) {
      delete campos[campo]
    }
  })

  const foto = campos.foto
  const quitarFoto = campos.quitar_foto === true
  delete campos.foto
  delete campos.quitar_foto

  // La foto que ya estaba llega como URL: no se reenvía, el backend la conserva.
  if (!(foto instanceof File) && !quitarFoto) {
    return campos
  }

  const formData = new FormData()
  Object.entries(campos).forEach(([campo, valor]) => {
    formData.append(campo, String(valor))
  })
  if (foto instanceof File) {
    formData.append('foto', foto)
  }
  if (quitarFoto) {
    formData.append('quitar_foto', 'true')
  }
  return formData
}

export const useProductos = (): UseProductosReturn => {
  const [productos, setProductos] = useState<ProductoList[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchProductos = async (params?: FetchProductosParams) => {
    setLoading(true)
    setError(null)
    try {
      // The API paginates at 20 by default, so without this the list silently
      // shows only the first page. A product catalog of this size does not need
      // paging; if it ever grows past a few hundred, add real controls instead
      // of raising this further (the backend caps page_size at 1000).
      const response = await api.get('/inventario/productos/', {
        params: { page_size: 200, ...params },
      })
      const data = Array.isArray(response.data) ? response.data : response.data.results || []
      setProductos(data)
    } catch (err: any) {
      setError(err.response?.data?.message || 'Error al cargar los productos')
      console.error('Error fetching productos:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchProducto = async (id: number): Promise<ProductoDetail | null> => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get(`/inventario/productos/${id}/`)
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.message || 'Error al cargar el producto')
      console.error('Error fetching producto:', err)
      return null
    } finally {
      setLoading(false)
    }
  }

  const createProducto = async (data: ProductoFormData): Promise<Producto | null> => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.post('/inventario/productos/', prepararPayload(data, false))
      return response.data
    } catch (err: any) {
      let errorMessage = 'Error al crear el producto:\n'
      const errors = err.response?.data

      if (errors) {
        Object.keys(errors).forEach(key => {
          const value = errors[key]
          const message = Array.isArray(value) ? value.join(', ') : value
          errorMessage += `${key}: ${message}\n`
        })
      }

      setError(errorMessage)
      console.error('Error creating producto:', err)
      throw err
    } finally {
      setLoading(false)
    }
  }

  const updateProducto = async (id: number, data: ProductoFormData): Promise<Producto | null> => {
    setLoading(true)
    setError(null)
    try {
      // PATCH y no PUT: el payload ya no lleva los campos de Conto, así que un
      // PUT los tomaría como faltantes y fallaría la validación de requeridos.
      const response = await api.patch(`/inventario/productos/${id}/`, prepararPayload(data, true))
      return response.data
    } catch (err: any) {
      let errorMessage = 'Error al actualizar el producto:\n'
      const errores = err.response?.data

      if (errores && typeof errores === 'object') {
        Object.keys(errores).forEach(campo => {
          const valor = errores[campo]
          errorMessage += `${campo}: ${Array.isArray(valor) ? valor.join(', ') : valor}\n`
        })
      }

      setError(errorMessage)
      console.error('Error updating producto:', err)
      throw err
    } finally {
      setLoading(false)
    }
  }

  const deleteProducto = async (id: number): Promise<boolean> => {
    setLoading(true)
    setError(null)
    try {
      await api.delete(`/inventario/productos/${id}/`)
      return true
    } catch (err: any) {
      setError(err.response?.data?.message || 'Error al eliminar el producto')
      console.error('Error deleting producto:', err)
      return false
    } finally {
      setLoading(false)
    }
  }

  const ajustarStock = async (id: number, data: AjustarStockData): Promise<boolean> => {
    setLoading(true)
    setError(null)
    try {
      await api.post(`/inventario/productos/${id}/ajustar_stock/`, data)
      return true
    } catch (err: any) {
      setError(err.response?.data?.error || 'Error al ajustar el stock')
      console.error('Error ajustando stock:', err)
      return false
    } finally {
      setLoading(false)
    }
  }

  const fetchStockBajo = async (): Promise<ProductoList[]> => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get('/inventario/productos/stock_bajo/')
      const data = Array.isArray(response.data) ? response.data : response.data.results || []
      return data
    } catch (err: any) {
      setError(err.response?.data?.message || 'Error al cargar productos con stock bajo')
      console.error('Error fetching stock bajo:', err)
      return []
    } finally {
      setLoading(false)
    }
  }

  const clearError = () => {
    setError(null)
  }

  return {
    productos,
    loading,
    error,
    fetchProductos,
    fetchProducto,
    createProducto,
    updateProducto,
    deleteProducto,
    ajustarStock,
    fetchStockBajo,
    clearError,
  }
}
