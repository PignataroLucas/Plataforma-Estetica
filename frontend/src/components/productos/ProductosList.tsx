import React from 'react'
import { Table, Badge, Button } from '../ui'
import type { ProductoList } from '../../types/models'

interface ProductosListProps {
  productos: ProductoList[]
  onEdit: (producto: ProductoList) => void
  onDelete: (producto: ProductoList) => void
  onAjustarStock: (producto: ProductoList) => void
  loading?: boolean
}

const getTipoBadgeVariant = (tipo: string): 'success' | 'warning' | 'info' | 'gray' => {
  switch (tipo) {
    case 'REVENTA':
      return 'success'
    case 'USO_INTERNO':
      return 'info'
    case 'INSUMO':
      return 'warning'
    default:
      return 'gray'
  }
}

const getTipoLabel = (tipo: string) => {
  const labels: Record<string, string> = {
    REVENTA: 'Reventa',
    USO_INTERNO: 'Uso Interno',
    INSUMO: 'Insumo',
  }
  return labels[tipo] || tipo
}

const formatPrice = (price: number) => {
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
    minimumFractionDigits: 0,
  }).format(price)
}

export const ProductosList: React.FC<ProductosListProps> = ({
  productos,
  onEdit,
  onDelete,
  onAjustarStock,
  loading,
}) => {
  const columns = [
    {
      key: 'nombre',
      header: 'Producto',
      accessor: (producto: ProductoList) => (
        <div className="flex flex-col">
          <span className="font-medium">{producto.nombre}</span>
          {producto.marca && <span className="text-sm text-gray-600">{producto.marca}</span>}
        </div>
      ),
    },
    {
      key: 'categoria',
      header: 'Categoría',
      accessor: (producto: ProductoList) => producto.categoria_nombre || <span className="text-gray-400 italic">Sin categoría</span>,
    },
    {
      key: 'tipo',
      header: 'Tipo',
      accessor: (producto: ProductoList) => (
        <Badge variant={getTipoBadgeVariant(producto.tipo)}>
          {getTipoLabel(producto.tipo)}
        </Badge>
      ),
    },
    {
      key: 'stock',
      header: 'Stock',
      accessor: (producto: ProductoList) => (
        <div className="flex flex-col items-center">
          <span className={`font-semibold ${producto.stock_bajo ? 'text-red-600' : 'text-gray-900'}`}>
            {producto.stock_actual} {producto.unidad_medida}
          </span>
          {producto.stock_bajo && (
            <span className="text-xs text-red-600">⚠️ Stock bajo</span>
          )}
        </div>
      ),
    },
    {
      key: 'precios',
      header: 'Precios',
      accessor: (producto: ProductoList) => (
        <div className="flex flex-col text-sm">
          <span className="text-gray-600">Costo: {formatPrice(producto.precio_costo)}</span>
          <span className="font-semibold">Venta: {formatPrice(producto.precio_venta)}</span>
          <span className="text-xs text-green-600">Margen: {producto.margen_ganancia.toFixed(1)}%</span>
        </div>
      ),
    },
    {
      key: 'proveedor',
      header: 'Proveedor',
      accessor: (producto: ProductoList) => producto.proveedor_nombre || <span className="text-gray-400 italic">-</span>,
    },
    {
      key: 'estado',
      header: 'Estado',
      accessor: (producto: ProductoList) => (
        <Badge variant={producto.activo ? 'success' : 'gray'}>
          {producto.activo ? 'Activo' : 'Inactivo'}
        </Badge>
      ),
    },
    {
      key: 'acciones',
      header: 'Acciones',
      accessor: (producto: ProductoList) => (
        <div className="flex gap-1 flex-wrap">
          <Button
            variant="primary"
            size="sm"
            onClick={() => onAjustarStock(producto)}
            title="Ajustar stock"
          >
            📦
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onEdit(producto)}
            title="Editar"
          >
            ✏️
          </Button>
          <Button
            variant="danger"
            size="sm"
            onClick={() => onDelete(producto)}
            title="Eliminar"
          >
            🗑️
          </Button>
        </div>
      ),
    },
  ]

  if (loading) {
    return <div className="text-center py-8">Cargando productos...</div>
  }

  if (productos.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No hay productos registrados. Crea el primero usando el botón "Nuevo Producto".
      </div>
    )
  }

  return <Table columns={columns} data={productos} />
}
