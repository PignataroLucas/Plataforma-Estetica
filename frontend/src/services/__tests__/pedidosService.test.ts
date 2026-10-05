/**
 * Las rutas que usa la bandeja de pedidos.
 *
 * El router del backend se monta en `api/turnos/` y registra `turnos` adentro
 * (`backend/apps/turnos/urls.py`), así que todo lleva el segmento dos veces. La
 * bandeja salió con uno solo y en producción las cuatro llamadas daban 404: la
 * página decía "no hay pedidos pendientes" con un pedido real esperando, y
 * aprobar o rechazar no habría andado tampoco.
 *
 * Los tests del backend no lo podían ver: arman la URL con `reverse()`, que
 * siempre da la ruta correcta. La mitad que falló es la que se escribe acá.
 *
 * Las rutas van literales a propósito, en vez de importar la constante del
 * servicio: un test que arma la URL con la misma constante pasa igual cuando
 * la constante está mal.
 */
import { AxiosHeaders, type AxiosAdapter, type InternalAxiosRequestConfig } from 'axios'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import api from '@/services/api'
import {
  aprobarPedido,
  getMotivosDeRechazo,
  getPedidosPendientes,
  rechazarPedido,
} from '@/services/pedidosService'

let ultimaPeticion: InternalAxiosRequestConfig | null = null
const adaptadorOriginal = api.defaults.adapter

const adaptadorEspia: AxiosAdapter = async (config) => {
  ultimaPeticion = config
  return {
    data: { count: 0, results: [] },
    status: 200,
    statusText: 'OK',
    headers: new AxiosHeaders(),
    config,
  }
}

const rutaPedida = (): string => {
  if (!ultimaPeticion) {
    throw new Error('El adaptador no llegó a recibir ninguna petición')
  }
  return ultimaPeticion.url ?? ''
}

beforeEach(() => {
  ultimaPeticion = null
  api.defaults.adapter = adaptadorEspia
})

afterEach(() => {
  // `api` es un singleton que comparte toda la suite.
  api.defaults.adapter = adaptadorOriginal
})

describe('las rutas de la bandeja de pedidos', () => {
  it('lista los pendientes en la ruta del viewset de turnos', async () => {
    await getPedidosPendientes()
    expect(rutaPedida()).toBe('/turnos/turnos/pendientes_de_aprobacion/')
  })

  it('pide los motivos de rechazo en la ruta del viewset de turnos', async () => {
    await getMotivosDeRechazo()
    expect(rutaPedida()).toBe('/turnos/turnos/motivos_de_rechazo/')
  })

  it('aprueba sobre el turno', async () => {
    await aprobarPedido(42)
    expect(rutaPedida()).toBe('/turnos/turnos/42/aprobar/')
  })

  it('rechaza sobre el turno', async () => {
    await rechazarPedido(42, 'SIN_DISPONIBILIDAD')
    expect(rutaPedida()).toBe('/turnos/turnos/42/rechazar/')
  })
})
