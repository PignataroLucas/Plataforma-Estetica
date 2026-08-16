import React, { useState, useEffect, useRef } from 'react'
import { Input, Select, Button } from '../ui'
import type { Producto, ProductoFormData, CategoriaProducto, Proveedor, TipoProducto } from '../../types/models'
import api from '../../services/api'

interface ProductoFormProps {
  initialData?: Partial<Producto>
  onSubmit: (data: ProductoFormData) => void
  onCancel: () => void
  submitLabel?: string
  formId?: string
  showButtons?: boolean
}

// Coincide con el tope que valida el backend.
const MAX_FOTO_BYTES = 5 * 1024 * 1024

/**
 * Un dato que administra el sync de Conto: se muestra pero no se edita ni se
 * manda al guardar, para que un guardado no lo revierta al valor que tenía
 * cuando se abrió el formulario.
 */
const CampoDeConto: React.FC<{ label: string; valor: React.ReactNode }> = ({ label, valor }) => (
  <div>
    <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
    <div className="px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-700">
      {valor ?? '—'}
    </div>
    <p className="mt-1 text-xs text-gray-500">Lo administra Conto</p>
  </div>
)

const tipoProductoOptions = [
  { value: 'REVENTA', label: 'Producto de Reventa' },
  { value: 'USO_INTERNO', label: 'Uso Interno' },
  { value: 'INSUMO', label: 'Insumo' },
]

const unidadMedidaOptions = [
  { value: 'UNIDAD', label: 'Unidad' },
  { value: 'ML', label: 'Mililitros (ML)' },
  { value: 'GR', label: 'Gramos (GR)' },
  { value: 'KG', label: 'Kilogramos (KG)' },
  { value: 'LT', label: 'Litros (LT)' },
]

export const ProductoForm: React.FC<ProductoFormProps> = ({
  initialData,
  onSubmit,
  onCancel,
  submitLabel = 'Guardar',
  formId = 'producto-form',
  showButtons = false,
}) => {
  const [formData, setFormData] = useState<Partial<Producto>>({
    tipo: 'REVENTA' as TipoProducto,
    unidad_medida: 'UNIDAD',
    activo: true,
    stock_actual: 0,
    stock_minimo: 0,
    ...initialData,
  })

  const [errors, setErrors] = useState<Partial<Record<keyof Producto, string>>>({})
  const [categorias, setCategorias] = useState<CategoriaProducto[]>([])
  const [proveedores, setProveedores] = useState<Proveedor[]>([])
  const [loadingData, setLoadingData] = useState(true)

  // Foto: el archivo nuevo, su vista previa y el pedido de borrar la que había.
  const [fotoNueva, setFotoNueva] = useState<File | null>(null)
  const [fotoPreview, setFotoPreview] = useState<string | null>(null)
  const [quitarFoto, setQuitarFoto] = useState(false)
  const [errorFoto, setErrorFoto] = useState<string | null>(null)
  const fotoInputRef = useRef<HTMLInputElement>(null)

  // Editar un producto que existe es el caso donde el sync de Conto puede pisar
  // datos; al crear uno nuevo hay que poder cargar costo y precio a mano.
  const esEdicion = Boolean(initialData?.id)
  const fotoActual = quitarFoto ? null : (fotoPreview || initialData?.foto || null)

  useEffect(() => {
    loadFormData()
  }, [])

  useEffect(() => {
    if (initialData) {
      setFormData({ ...formData, ...initialData })
    }
  }, [initialData])

  // La URL del objeto vive mientras se ve la vista previa; si no se libera,
  // cargar 31 fotos seguidas deja 31 blobs colgados en memoria.
  useEffect(() => {
    return () => {
      if (fotoPreview) URL.revokeObjectURL(fotoPreview)
    }
  }, [fotoPreview])

  const handleFotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const archivo = e.target.files?.[0]
    if (!archivo) return

    if (!archivo.type.startsWith('image/')) {
      setErrorFoto('El archivo tiene que ser una imagen (JPG, PNG o WebP)')
      e.target.value = ''
      return
    }
    if (archivo.size > MAX_FOTO_BYTES) {
      setErrorFoto(
        `La foto pesa ${(archivo.size / (1024 * 1024)).toFixed(1)} MB y el máximo es 5 MB`
      )
      e.target.value = ''
      return
    }

    if (fotoPreview) URL.revokeObjectURL(fotoPreview)
    setErrorFoto(null)
    setQuitarFoto(false)
    setFotoNueva(archivo)
    setFotoPreview(URL.createObjectURL(archivo))
  }

  const handleQuitarFoto = () => {
    if (fotoPreview) URL.revokeObjectURL(fotoPreview)
    setFotoPreview(null)
    setFotoNueva(null)
    setErrorFoto(null)
    // Solo hay algo que borrar en el servidor si el producto ya tenía foto.
    setQuitarFoto(Boolean(initialData?.foto))
    if (fotoInputRef.current) fotoInputRef.current.value = ''
  }

  const loadFormData = async () => {
    setLoadingData(true)
    try {
      const [categoriasRes, proveedoresRes] = await Promise.all([
        api.get('/inventario/categorias/'),
        api.get('/inventario/proveedores/?activo=true'),
      ])

      const categoriasData = Array.isArray(categoriasRes.data) ? categoriasRes.data : categoriasRes.data.results || []
      const proveedoresData = Array.isArray(proveedoresRes.data) ? proveedoresRes.data : proveedoresRes.data.results || []

      setCategorias(categoriasData)
      setProveedores(proveedoresData)
    } catch (err) {
      console.error('Error loading form data:', err)
    } finally {
      setLoadingData(false)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target
    const checked = (e.target as HTMLInputElement).checked

    let processedValue: any = value

    // Convert number inputs to actual numbers
    if (type === 'number' && value !== '') {
      processedValue = parseFloat(value)
    } else if (type === 'checkbox') {
      processedValue = checked
    }

    setFormData(prev => ({
      ...prev,
      [name]: processedValue
    }))

    if (errors[name as keyof Producto]) {
      setErrors(prev => ({ ...prev, [name]: undefined }))
    }
  }

  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof Producto, string>> = {}

    // Convert to numbers for comparison (handle both number and string inputs)
    const costo = Number(formData.precio_costo)
    const venta = Number(formData.precio_venta)
    const efectivo = formData.precio_efectivo ? Number(formData.precio_efectivo) : null
    const transferencia = formData.precio_transferencia ? Number(formData.precio_transferencia) : null
    const debito = formData.precio_debito ? Number(formData.precio_debito) : null
    const credito = formData.precio_credito ? Number(formData.precio_credito) : null

    if (!formData.nombre?.trim()) {
      newErrors.nombre = 'El nombre es requerido'
    }

    // Al editar, costo y precio no se tocan ni se mandan: los administra Conto.
    if (!esEdicion) {
      if (!formData.precio_costo || costo <= 0) {
        newErrors.precio_costo = 'El precio de costo debe ser mayor a 0'
      }
      if (!formData.precio_venta || venta <= 0) {
        newErrors.precio_venta = 'El precio de venta debe ser mayor a 0'
      }
      if (formData.precio_venta && formData.precio_costo && venta < costo) {
        newErrors.precio_venta = 'El precio de venta debe ser mayor al costo'
      }
    }

    // Validate payment method prices (if specified)
    if (costo > 0) {
      if (efectivo !== null && efectivo < costo) {
        newErrors.precio_efectivo = 'El precio en efectivo debe ser mayor al costo'
      }
      if (transferencia !== null && transferencia < costo) {
        newErrors.precio_transferencia = 'El precio de transferencia debe ser mayor al costo'
      }
      if (debito !== null && debito < costo) {
        newErrors.precio_debito = 'El precio de débito debe ser mayor al costo'
      }
      if (credito !== null && credito < costo) {
        newErrors.precio_credito = 'El precio de crédito debe ser mayor al costo'
      }
    }

    if (formData.stock_minimo && Number(formData.stock_minimo) < 0) {
      newErrors.stock_minimo = 'El stock mínimo no puede ser negativo'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!validateForm()) return

    onSubmit({
      ...formData,
      // La foto solo viaja si es un archivo nuevo; la que ya estaba es una URL
      // y el backend la conserva sola.
      foto: fotoNueva,
      quitar_foto: quitarFoto,
    })
  }

  const categoriaOptions = [
    { value: '', label: 'Sin categoría' },
    ...categorias.map(c => ({
      value: c.id.toString(),
      label: c.nombre,
    })),
  ]

  const proveedorOptions = [
    { value: '', label: 'Sin proveedor' },
    ...proveedores.map(p => ({
      value: p.id.toString(),
      label: p.nombre,
    })),
  ]

  // Calcular margen automáticamente basado en precio de efectivo (principal)
  const precioBase = formData.precio_efectivo || formData.precio_venta
  const margen = formData.precio_costo && precioBase
    ? ((precioBase - formData.precio_costo) / formData.precio_costo) * 100
    : 0

  if (loadingData) {
    return <div className="p-4 text-center">Cargando datos del formulario...</div>
  }

  return (
    <form id={formId} onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="col-span-2">
          <Input
            label="Nombre del Producto"
            name="nombre"
            value={formData.nombre || ''}
            onChange={handleChange}
            required
            error={errors.nombre}
            placeholder="Ej: Crema hidratante, Aceite esencial..."
          />
        </div>

        <Select
          label="Categoría"
          name="categoria"
          value={formData.categoria?.toString() || ''}
          onChange={handleChange}
          options={categoriaOptions}
        />

        <Select
          label="Tipo de Producto"
          name="tipo"
          value={formData.tipo || 'REVENTA'}
          onChange={handleChange}
          options={tipoProductoOptions}
          required
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Input
          label="Marca"
          name="marca"
          value={formData.marca || ''}
          onChange={handleChange}
          placeholder="Opcional"
        />

        <Select
          label="Proveedor"
          name="proveedor"
          value={formData.proveedor?.toString() || ''}
          onChange={handleChange}
          options={proveedorOptions}
        />
      </div>

      <div className="grid grid-cols-3 gap-4">
        <Input
          label="SKU"
          name="sku"
          value={formData.sku || ''}
          onChange={handleChange}
          placeholder="Código interno"
        />

        <Input
          label="Código de Barras"
          name="codigo_barras"
          value={formData.codigo_barras || ''}
          onChange={handleChange}
          placeholder="Opcional"
        />

        <Input
          label="Producto en Tienda Nube"
          name="tiendanube_product_id"
          value={formData.tiendanube_product_id || ''}
          onChange={handleChange}
          placeholder="Sin esto no se puede comprar desde la app"
        />

        <Input
          label="Variante en Tienda Nube"
          name="tiendanube_variant_id"
          value={formData.tiendanube_variant_id || ''}
          onChange={handleChange}
          placeholder="Solo si el producto tiene más de una"
        />

        <Select
          label="Unidad de Medida"
          name="unidad_medida"
          value={formData.unidad_medida || 'UNIDAD'}
          onChange={handleChange}
          options={unidadMedidaOptions}
          required
        />
      </div>

      <div className="p-4 bg-blue-50 border border-blue-200 rounded-md">
        <h4 className="text-sm font-semibold text-blue-900 mb-3">Stock</h4>
        <div className="grid grid-cols-3 gap-4">
          {esEdicion ? (
            <CampoDeConto
              label="Stock Actual"
              valor={`${formData.stock_actual ?? 0} ${formData.unidad_medida || ''}`.trim()}
            />
          ) : (
            <Input
              label="Stock Actual"
              name="stock_actual"
              type="number"
              step="0.01"
              value={formData.stock_actual?.toString() || '0'}
              onChange={handleChange}
              required
            />
          )}

          <Input
            label="Stock Mínimo"
            name="stock_minimo"
            type="number"
            step="0.01"
            value={formData.stock_minimo?.toString() || '0'}
            onChange={handleChange}
            required
            error={errors.stock_minimo}
          />

          <Input
            label="Stock Máximo"
            name="stock_maximo"
            type="number"
            step="0.01"
            value={formData.stock_maximo?.toString() || ''}
            onChange={handleChange}
            placeholder="Opcional"
          />
        </div>
      </div>

      <div className="p-4 bg-green-50 border border-green-200 rounded-md">
        <h4 className="text-sm font-semibold text-green-900 mb-3">Precios</h4>

        <div className="grid grid-cols-2 gap-4 mb-4">
          {esEdicion ? (
            <>
              <CampoDeConto
                label="Precio de Costo"
                valor={formData.precio_costo != null ? `$${formData.precio_costo}` : null}
              />
              <CampoDeConto
                label="Precio de Venta (Base)"
                valor={formData.precio_venta != null ? `$${formData.precio_venta}` : null}
              />
            </>
          ) : (
            <>
              <Input
                label="Precio de Costo"
                name="precio_costo"
                type="number"
                step="0.01"
                value={formData.precio_costo?.toString() || ''}
                onChange={handleChange}
                required
                error={errors.precio_costo}
                placeholder="$0.00"
              />

              <Input
                label="Precio de Venta (Base)"
                name="precio_venta"
                type="number"
                step="0.01"
                value={formData.precio_venta?.toString() || ''}
                onChange={handleChange}
                required
                error={errors.precio_venta}
                placeholder="$0.00"
              />
            </>
          )}
        </div>

        <div className="border-t border-green-300 pt-3 mb-3">
          <p className="text-xs text-green-800 mb-3 font-medium">Precios por Método de Pago (opcionales)</p>
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="💵 Precio en Efectivo"
              name="precio_efectivo"
              type="number"
              step="0.01"
              value={formData.precio_efectivo?.toString() || ''}
              onChange={handleChange}
              error={errors.precio_efectivo}
              placeholder="Opcional"
            />

            <Input
              label="🏦 Precio Transferencia"
              name="precio_transferencia"
              type="number"
              step="0.01"
              value={formData.precio_transferencia?.toString() || ''}
              onChange={handleChange}
              error={errors.precio_transferencia}
              placeholder="Opcional"
            />

            <Input
              label="💳 Precio Débito"
              name="precio_debito"
              type="number"
              step="0.01"
              value={formData.precio_debito?.toString() || ''}
              onChange={handleChange}
              error={errors.precio_debito}
              placeholder="Opcional"
            />

            <Input
              label="💳 Precio Crédito"
              name="precio_credito"
              type="number"
              step="0.01"
              value={formData.precio_credito?.toString() || ''}
              onChange={handleChange}
              error={errors.precio_credito}
              placeholder="Opcional"
            />
          </div>
          <p className="text-xs text-green-700 mt-2 italic">
            💡 El precio en efectivo se usa como precio principal. Si no se especifican precios por método de pago, se usa el precio de venta base.
          </p>
          {/* TODO: Implementar precios por cantidad de cuotas para tarjeta de crédito */}
        </div>

        {margen > 0 && (
          <div className="mt-3 pt-3 border-t border-green-300 text-sm text-green-700">
            <strong>Margen de ganancia (basado en efectivo):</strong> {margen.toFixed(1)}%
          </div>
        )}
      </div>

      <div className="p-4 bg-purple-50 border border-purple-200 rounded-md">
        <h4 className="text-sm font-semibold text-purple-900 mb-1">Contenido para el catálogo</h4>
        <p className="text-xs text-purple-800 mb-3">
          La foto y la descripción son lo que ve la clienta en la app. El sync de Conto no las toca.
        </p>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <span className="block text-sm font-medium text-gray-700 mb-1">Foto</span>
            <div className="aspect-square w-full rounded-lg border border-purple-200 bg-white overflow-hidden flex items-center justify-center">
              {fotoActual ? (
                <img src={fotoActual} alt="Vista previa del producto" className="w-full h-full object-contain" />
              ) : (
                <span className="text-xs text-gray-400 text-center px-2">Sin foto</span>
              )}
            </div>
          </div>

          <div className="col-span-2 flex flex-col justify-center gap-2">
            <input
              ref={fotoInputRef}
              type="file"
              accept="image/*"
              onChange={handleFotoChange}
              className="block w-full text-sm text-gray-700 file:mr-3 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-purple-100 file:text-purple-800 file:text-sm file:font-medium hover:file:bg-purple-200"
            />
            {errorFoto ? (
              <p className="text-sm text-red-600">{errorFoto}</p>
            ) : (
              <p className="text-xs text-gray-500">
                JPG, PNG o WebP, hasta 5 MB. La miniatura para la grilla se genera sola.
              </p>
            )}
            {fotoActual && (
              <button
                type="button"
                onClick={handleQuitarFoto}
                className="self-start text-sm text-red-600 hover:text-red-800 underline"
              >
                Quitar foto
              </button>
            )}
            {quitarFoto && (
              <p className="text-xs text-red-600">
                La foto se va a borrar al guardar.
              </p>
            )}
          </div>
        </div>

        <div className="mt-4">
          <label htmlFor="descripcion" className="block text-sm font-medium text-gray-700 mb-1">
            Qué es
          </label>
          <textarea
            id="descripcion"
            name="descripcion"
            value={formData.descripcion || ''}
            onChange={handleChange}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Qué es, para qué tipo de piel, cómo se usa..."
          />
        </div>

        <div className="mt-4">
          <label htmlFor="beneficios" className="block text-sm font-medium text-gray-700 mb-1">
            Beneficios
          </label>
          <textarea
            id="beneficios"
            name="beneficios"
            value={formData.beneficios || ''}
            onChange={handleChange}
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder={'Un beneficio por línea:\nHidrata sin sensación grasa\nCalma la piel después del sol'}
          />
          <p className="mt-1 text-xs text-purple-800">
            Una línea por beneficio. La app los muestra como lista, igual que en los tratamientos.
          </p>
        </div>
      </div>

      <div className="flex items-center">
        <input
          type="checkbox"
          id="activo"
          name="activo"
          checked={formData.activo || false}
          onChange={handleChange}
          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
        />
        <label htmlFor="activo" className="ml-2 block text-sm text-gray-900">
          Producto activo
        </label>
      </div>

      {showButtons && (
        <div className="flex gap-2 justify-end">
          <Button type="button" variant="secondary" onClick={onCancel}>
            Cancelar
          </Button>
          <Button type="submit" variant="primary">
            {submitLabel}
          </Button>
        </div>
      )}
    </form>
  )
}
