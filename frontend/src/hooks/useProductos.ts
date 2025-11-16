import { useState } from 'react'
import api from '../services/api'
import type { Producto, ProductoList, ProductoDetail, TipoMovimiento } from '../types/models'

interface UseProductosReturn {
  productos: ProductoList[]
  loading: boolean
  error: string | null
  fetchProductos: (params?: FetchProductosParams) => Promise<void>
  fetchProducto: (id: number) => Promise<ProductoDetail | null>
  createProducto: (data: Partial<Producto>) => Promise<Producto | null>
  updateProducto: (id: number, data: Partial<Producto>) => Promise<Producto | null>
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

export const useProductos = (): UseProductosReturn => {
  const [productos, setProductos] = useState<ProductoList[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const cleanProductoData = (data: Partial<Producto>) => {
    const cleaned: any = { ...data }
    const optionalFields = ['categoria', 'proveedor', 'descripcion', 'marca', 'codigo_barras', 'sku', 'stock_maximo', 'foto']

    optionalFields.forEach(field => {
      if (cleaned[field] === '' || cleaned[field] === undefined || cleaned[field] === null) {
        delete cleaned[field]
      }
    })

    return cleaned
  }

  const fetchProductos = async (params?: FetchProductosParams) => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get('/inventario/productos/', { params })
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

  const createProducto = async (data: Partial<Producto>): Promise<Producto | null> => {
    setLoading(true)
    setError(null)
    try {
      const cleanedData = cleanProductoData(data)
      const response = await api.post('/inventario/productos/', cleanedData)
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

  const updateProducto = async (id: number, data: Partial<Producto>): Promise<Producto | null> => {
    setLoading(true)
    setError(null)
    try {
      const cleanedData = cleanProductoData(data)
      const response = await api.put(`/inventario/productos/${id}/`, cleanedData)
      return response.data
    } catch (err: any) {
      const errorMessage = err.response?.data?.message || 'Error al actualizar el producto'
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
