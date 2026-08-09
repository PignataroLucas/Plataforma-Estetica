/**
 * Qué campos viajan cuando el CRM guarda un producto.
 *
 * El reparto es sin superposición: Conto manda sobre stock, costo y precio; el
 * centro manda sobre foto, descripción y nombre (INTEGRACION_CATALOGO_SPEC.md
 * §5.2). El defecto que esto previene es el cruce de ese límite, y es
 * silencioso: el CRM guardaba mandando el formulario entero, así que un
 * formulario abierto a las 10:00 y guardado a las 10:10 revertía a los valores
 * de las 10:00 lo que el sync había escrito a las 10:05. Sin error, sin 500,
 * hasta la próxima sincronización.
 *
 * El backend cubre su mitad en
 * `backend/apps/inventario/tests/test_foto_producto.py`
 * (`test_guardar_contenido_no_revierte_lo_que_dejo_el_sync_de_conto`): que un
 * guardado sin esos campos los deje intactos. La otra mitad —que el CRM no los
 * mande— se decide acá, y es la que estos tests sostienen.
 *
 * Las listas de campos se escriben literales a propósito, en vez de importar
 * las constantes del módulo: si alguien vacía `CAMPOS_DE_CONTO`, un test que
 * itera esa misma constante pasa igual sin probar nada.
 */
import { describe, expect, it } from 'vitest'

import { prepararPayload } from '../useProductos'
import { TipoProducto, type ProductoFormData } from '@/types/models'

// El segundo argumento de prepararPayload, con nombre: `false` en la llamada no
// dice nada sobre qué caso se está probando.
const EDITANDO = true
const CREANDO = false

/**
 * Lo que arma ProductoForm al guardar.
 *
 * `extras` entra sin tipar porque en el CRM real llegan por acá campos que
 * `ProductoFormData` no nombra: el formulario se inicializa con `initialData`,
 * que es la respuesta cruda de la API (id, sucursal, margen_ganancia,
 * categoria_data...). Que sobren campos no es un caso hipotético, es el caso
 * normal, y es la razón de ser de la lista de solo lectura.
 */
const productoDelFormulario = (extras: Record<string, unknown> = {}): ProductoFormData =>
  ({
    nombre: 'Crema Multivitamínica',
    descripcion: 'Ilumina y unifica el tono.',
    marca: 'Ame',
    sku: 'CRM-001',
    tipo: TipoProducto.REVENTA,
    unidad_medida: 'UNIDAD',
    stock_minimo: 2,
    activo: true,
    // Los tres que administra el sync.
    stock_actual: 9,
    precio_costo: 777,
    precio_venta: 1500,
    ...extras,
  }) as ProductoFormData

const unaFoto = (nombre = 'crema.jpg') =>
  new File(['datos de la imagen'], nombre, { type: 'image/jpeg' })

/** El payload cuando se esperaba un JSON, con el fallo explicado si no lo es. */
const comoJson = (payload: FormData | Record<string, unknown>): Record<string, unknown> => {
  if (payload instanceof FormData) {
    throw new Error('Se esperaba un objeto plano (JSON) y salió un FormData')
  }
  return payload
}

/** El payload cuando se esperaba un multipart. */
const comoFormData = (payload: FormData | Record<string, unknown>): FormData => {
  if (!(payload instanceof FormData)) {
    throw new Error(
      `Se esperaba un FormData y salió un objeto plano: ${JSON.stringify(payload)}`
    )
  }
  return payload
}

describe('prepararPayload', () => {
  describe('los campos que administra el sync de Conto', () => {
    it('no viajan al editar', () => {
      const payload = comoJson(prepararPayload(productoDelFormulario(), EDITANDO))

      expect(payload).not.toHaveProperty('stock_actual')
      expect(payload).not.toHaveProperty('precio_costo')
      expect(payload).not.toHaveProperty('precio_venta')
      // Y lo que el centro sí edita tiene que seguir viajando: un payload vacío
      // también pasaría las tres afirmaciones de arriba.
      expect(payload.descripcion).toBe('Ilumina y unifica el tono.')
      expect(payload.nombre).toBe('Crema Multivitamínica')
    })

    it('tampoco viajan al editar cuando el guardado lleva foto', () => {
      // El multipart se arma por otra rama de la función. Es justo el guardado
      // con más chances de tener el formulario abierto un rato largo —cargar
      // fotos de a decenas— así que la omisión tiene que valer también acá.
      const payload = comoFormData(
        prepararPayload(productoDelFormulario({ foto: unaFoto() }), EDITANDO)
      )

      expect(payload.has('stock_actual')).toBe(false)
      expect(payload.has('precio_costo')).toBe(false)
      expect(payload.has('precio_venta')).toBe(false)
      expect(payload.get('descripcion')).toBe('Ilumina y unifica el tono.')
    })

    it('sí viajan al crear', () => {
      // Un producto que todavía no existe en Conto no tiene quién le ponga
      // costo ni precio: si se omitieran acá, el alta fallaría por requeridos.
      const payload = comoJson(prepararPayload(productoDelFormulario(), CREANDO))

      expect(payload.stock_actual).toBe(9)
      expect(payload.precio_costo).toBe(777)
      expect(payload.precio_venta).toBe(1500)
    })
  })

  describe('la foto', () => {
    it('viaja como multipart cuando es un archivo nuevo', () => {
      const archivo = unaFoto()

      const payload = comoFormData(
        prepararPayload(productoDelFormulario({ foto: archivo }), EDITANDO)
      )

      expect(payload.get('foto')).toBe(archivo)
    })

    it('no se reenvía cuando es la que ya estaba', () => {
      // Una foto guardada vuelve del backend como URL. Reenviarla como texto
      // dejaría el campo con la cadena en vez del archivo, y de paso obligaría
      // a un multipart en el guardado más común del CRM, que es solo texto.
      const payload = comoJson(
        prepararPayload(
          productoDelFormulario({ foto: 'https://ame-catalogo.s3.amazonaws.com/crema.jpg' }),
          EDITANDO
        )
      )

      expect(payload).not.toHaveProperty('foto')
      // `quitar_foto: false` es una señal para esta función, no un campo del
      // modelo: no tiene por qué llegar al backend.
      expect(payload).not.toHaveProperty('quitar_foto')
    })

    it('quitar_foto obliga al multipart aunque no haya archivo nuevo', () => {
      // Borrar la foto es lo único que no se puede expresar sin multipart: un
      // JSON con `foto: null` no distingue "no la toques" de "borrala", y por
      // eso existe la señal aparte. Si esta rama volviera a JSON, el botón
      // "Quitar foto" no haría nada y nadie se enteraría hasta ver la app.
      const payload = comoFormData(
        prepararPayload(
          productoDelFormulario({
            foto: 'https://ame-catalogo.s3.amazonaws.com/crema.jpg',
            quitar_foto: true,
          }),
          EDITANDO
        )
      )

      expect(payload.get('quitar_foto')).toBe('true')
      expect(payload.has('foto')).toBe(false)
    })
  })

  it('no manda los campos de solo lectura que llegaron en initialData', () => {
    // El formulario se llena con la respuesta de la API, así que estos entran
    // solos. El serializer los ignora o se queja, según el campo; en ninguno de
    // los dos casos tienen por qué salir del CRM.
    const payload = comoJson(
      prepararPayload(
        productoDelFormulario({
          id: 31,
          sucursal: 1,
          foto_thumb: 'https://ame-catalogo.s3.amazonaws.com/thumbs/crema.webp',
          creado_en: '2026-08-01T10:00:00Z',
          actualizado_en: '2026-08-09T10:05:00Z',
          margen_ganancia: 92.7,
          stock_bajo: false,
          categoria_nombre: 'Facial',
          proveedor_nombre: 'Distribuidora Norte',
          categoria_data: { id: 3, nombre: 'Facial' },
          proveedor_data: { id: 4, nombre: 'Distribuidora Norte' },
        }),
        EDITANDO
      )
    )

    expect(Object.keys(payload).sort()).toEqual([
      'activo',
      'descripcion',
      'marca',
      'nombre',
      'sku',
      'stock_minimo',
      'tipo',
      'unidad_medida',
    ])
  })

  it('no manda en blanco los opcionales que el backend no acepta vacíos', () => {
    // Un `<select>` sin elegir y un `<input type="number">` en blanco valen ''.
    // Mandados así son un 400 por campo: '' no es una FK ni un decimal. El
    // formulario tiene cuatro precios opcionales, con lo cual es el error más
    // fácil de provocar sin hacer nada raro.
    const payload = comoJson(
      prepararPayload(
        productoDelFormulario({
          categoria: '',
          proveedor: '',
          codigo_barras: '',
          stock_maximo: '',
          precio_efectivo: '',
          precio_transferencia: '',
          precio_debito: '',
          precio_credito: '',
        }),
        EDITANDO
      )
    )

    expect(payload).not.toHaveProperty('categoria')
    expect(payload).not.toHaveProperty('proveedor')
    expect(payload).not.toHaveProperty('stock_maximo')
    expect(payload).not.toHaveProperty('precio_efectivo')
    // La descripción, en cambio, se manda vacía a propósito: es como se borra
    // un texto que ya estaba cargado.
    const vaciada = comoJson(
      prepararPayload(productoDelFormulario({ descripcion: '' }), EDITANDO)
    )
    expect(vaciada.descripcion).toBe('')
  })
})
