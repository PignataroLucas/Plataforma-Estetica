/**
 * El interceptor que saca el Content-Type cuando el cuerpo es un FormData.
 *
 * La instancia de axios nace con `Content-Type: application/json`, que es lo
 * correcto para casi todo el CRM y veneno para una subida de archivo.
 *
 * El daño no es el que uno esperaría. Verificado contra axios 1.13: su
 * `transformRequest` mira el Content-Type y, si dice JSON, **serializa el
 * FormData a JSON** antes de que el request salga. El archivo se convierte en
 * `{}` y lo que viaja es `{"descripcion":"Ilumina","foto":{}}`. La foto no
 * llega mal: no llega. El backend contesta 200 porque el resto del formulario
 * es válido, el producto se queda sin foto y nada avisa.
 *
 * Por eso el test mira el cuerpo y no el header. El header, en el medio del
 * camino, no significa lo que parece: `dispatchRequest` vuelve a poner
 * `application/x-www-form-urlencoded` en todo POST/PUT/PATCH, y recién el
 * adaptador (`helpers/resolveConfig`) lo borra para que el navegador ponga el
 * suyo con el boundary. Afirmar "no hay Content-Type" sería afirmar sobre un
 * estado intermedio de axios. Lo que el interceptor garantiza es más acotado y
 * es lo que importa: que un cuerpo FormData nunca lleve el Content-Type de JSON.
 */
import { AxiosHeaders, type AxiosAdapter, type InternalAxiosRequestConfig } from 'axios'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import api from '@/services/api'

let ultimaPeticion: InternalAxiosRequestConfig | null = null
const adaptadorOriginal = api.defaults.adapter

/**
 * Corta el request justo antes de la red, con los interceptores y las
 * transformaciones de axios ya aplicadas: ahí es donde vive el defecto.
 */
const adaptadorEspia: AxiosAdapter = async (config) => {
  ultimaPeticion = config
  return { data: {}, status: 200, statusText: 'OK', headers: new AxiosHeaders(), config }
}

const peticionEspiada = (): InternalAxiosRequestConfig => {
  if (!ultimaPeticion) {
    throw new Error('El adaptador no llegó a recibir ninguna petición')
  }
  return ultimaPeticion
}

beforeEach(() => {
  ultimaPeticion = null
  api.defaults.adapter = adaptadorEspia
})

afterEach(() => {
  // `api` es un singleton que comparte toda la suite.
  api.defaults.adapter = adaptadorOriginal
})

const guardadoConFoto = () => {
  const foto = new File(['bytes de la imagen'], 'crema.jpg', { type: 'image/jpeg' })
  const cuerpo = new FormData()
  cuerpo.append('descripcion', 'Ilumina y unifica el tono.')
  cuerpo.append('foto', foto)
  return { foto, cuerpo }
}

describe('el interceptor de request', () => {
  it('deja salir el archivo entero cuando el cuerpo es un FormData', async () => {
    const { foto, cuerpo } = guardadoConFoto()

    await api.patch('/inventario/productos/31/', cuerpo)

    // Sigue siendo un FormData y adentro está el archivo: no lo aplastó nadie
    // a `{}` ni a la cadena "[object File]".
    const enviado = peticionEspiada().data
    expect(enviado).toBeInstanceOf(FormData)
    expect((enviado as FormData).get('foto')).toBe(foto)
    expect((enviado as FormData).get('descripcion')).toBe('Ilumina y unifica el tono.')
  })

  it('no deja el Content-Type de JSON sobre un cuerpo FormData', async () => {
    // La condición exacta de la que depende `transformRequest` para decidir si
    // serializa. Es la línea que el interceptor existe para evitar.
    const { cuerpo } = guardadoConFoto()

    await api.patch('/inventario/productos/31/', cuerpo)

    expect(peticionEspiada().headers.getContentType()).not.toContain('application/json')
  })

  it('el guardado sin archivo sigue viajando como JSON', async () => {
    // La otra mitad: sacar el header de más no puede habérselo sacado a todos.
    // Este es el camino del 99% del CRM y se rompería en silencio igual de bien.
    await api.patch('/inventario/productos/31/', { descripcion: 'Textura ligera' })

    expect(peticionEspiada().headers.getContentType()).toContain('application/json')
    expect(peticionEspiada().data).toBe('{"descripcion":"Textura ligera"}')
  })
})
