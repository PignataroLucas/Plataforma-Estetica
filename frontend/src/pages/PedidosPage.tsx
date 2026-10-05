import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { Clock, Check, X, Phone, Inbox } from 'lucide-react'
import toast from 'react-hot-toast'

import { Button, Card, CardBody, Spinner } from '@/components/ui'
import RechazarPedidoModal from '@/components/turnos/RechazarPedidoModal'
import { PEDIDOS_KEY, usePedidosPendientes } from '@/hooks/usePedidosPendientes'
import {
  PedidoYaResuelto,
  aprobarPedido,
  rechazarPedido,
  type PedidoPendiente,
} from '@/services/pedidosService'

/**
 * La cola de pedidos de turno que llegan desde la app.
 *
 * Es una **cola de trabajo**, no la agenda: por eso vive separada de Turnos. Lo
 * único que hay que resolver acá es sí o no, y la pantalla está armada para eso
 * — todo lo que hace falta para decidir a la vista, y dos botones.
 *
 * El mail que recibe el centro linkea a `/pedidos?turno=<id>`, así que la ficha
 * que viene en la URL se resalta al entrar.
 */
export default function PedidosPage() {
  const { pedidos, cargando, error } = usePedidosPendientes()
  const queryClient = useQueryClient()
  const [params] = useSearchParams()
  const [rechazando, setRechazando] = useState<PedidoPendiente | null>(null)
  const [guardando, setGuardando] = useState<number | null>(null)

  const destacado = Number(params.get('turno')) || null
  const refDestacado = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Viene del link del mail: llevarla al pedido en vez de hacerla buscar.
    refDestacado.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, [destacado, pedidos.length])

  const refrescar = () => queryClient.invalidateQueries({ queryKey: PEDIDOS_KEY })

  /**
   * Un 409 no es un error: alguien del centro lo resolvió primero. Se dice con
   * todas las letras y se refresca, para que no quede un pedido fantasma en
   * pantalla.
   */
  const manejarConflicto = (error: unknown) => {
    if (error instanceof PedidoYaResuelto) {
      toast(error.message, { icon: '👀' })
    } else {
      toast.error('No se pudo guardar. Probá de nuevo.')
    }
    refrescar()
  }

  const aprobar = async (pedido: PedidoPendiente) => {
    setGuardando(pedido.id)
    try {
      await aprobarPedido(pedido.id)
      toast.success(`Turno de ${pedido.cliente_nombre} confirmado`)
      refrescar()
    } catch (error) {
      manejarConflicto(error)
    } finally {
      setGuardando(null)
    }
  }

  const rechazar = async (motivo: string, detalle: string) => {
    if (!rechazando) return
    setGuardando(rechazando.id)
    try {
      await rechazarPedido(rechazando.id, motivo, detalle)
      toast.success('Pedido rechazado. Le avisamos a la clienta.')
      setRechazando(null)
      refrescar()
    } catch (error) {
      manejarConflicto(error)
    } finally {
      setGuardando(null)
    }
  }

  if (cargando) {
    return (
      <div className="flex justify-center py-16">
        <Spinner />
      </div>
    )
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Pedidos de la app</h1>
        <p className="text-sm text-gray-600 mt-1">
          Turnos que pidieron tus clientas y están esperando tu respuesta.
        </p>
      </div>

      {error ? (
        <Card>
          <CardBody>
            <div className="text-center py-12">
              <Inbox className="w-10 h-10 text-red-300 mx-auto mb-3" />
              <p className="text-gray-900 font-medium">No pudimos cargar los pedidos</p>
              <p className="text-sm text-gray-500 mt-1">
                Puede haber pedidos esperando. Reintentamos solos cada 30 segundos.
              </p>
            </div>
          </CardBody>
        </Card>
      ) : pedidos.length === 0 ? (
        <Card>
          <CardBody>
            <div className="text-center py-12">
              <Inbox className="w-10 h-10 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-900 font-medium">No hay pedidos pendientes</p>
              <p className="text-sm text-gray-500 mt-1">
                Cuando alguien reserve desde la app, lo vas a ver acá.
              </p>
            </div>
          </CardBody>
        </Card>
      ) : (
        <div className="space-y-3">
          {pedidos.map((pedido) => (
            <div key={pedido.id} ref={pedido.id === destacado ? refDestacado : undefined}>
              <FilaDePedido
                pedido={pedido}
                destacado={pedido.id === destacado}
                guardando={guardando === pedido.id}
                onAprobar={() => aprobar(pedido)}
                onRechazar={() => setRechazando(pedido)}
              />
            </div>
          ))}
        </div>
      )}

      {rechazando && (
        <RechazarPedidoModal
          pedido={rechazando}
          guardando={guardando === rechazando.id}
          onCancelar={() => setRechazando(null)}
          onConfirmar={rechazar}
        />
      )}
    </div>
  )
}

function FilaDePedido({
  pedido,
  destacado,
  guardando,
  onAprobar,
  onRechazar,
}: {
  pedido: PedidoPendiente
  destacado: boolean
  guardando: boolean
  onAprobar: () => void
  onRechazar: () => void
}) {
  const inicio = new Date(pedido.fecha_hora_inicio)

  return (
    <Card className={destacado ? 'ring-2 ring-primary-500' : ''}>
      <CardBody>
        <div className="flex items-start gap-4">
          <div className="flex-1 min-w-0">
            <p className="font-medium text-gray-900">{pedido.cliente_nombre}</p>
            <p className="text-sm text-gray-600">{pedido.servicio_nombre}</p>

            <p className="text-sm text-gray-900 mt-2">
              {inicio.toLocaleDateString('es-AR', {
                weekday: 'long',
                day: 'numeric',
                month: 'long',
              })}
              {' a las '}
              {inicio.toLocaleTimeString('es-AR', {
                hour: '2-digit',
                minute: '2-digit',
              })}
            </p>

            {pedido.cliente_telefono && (
              <p className="text-sm text-gray-500 mt-1 flex items-center gap-1">
                <Phone className="w-3.5 h-3.5" />
                {pedido.cliente_telefono}
              </p>
            )}

            {pedido.notas && (
              <p className="text-sm text-gray-600 mt-2 italic">“{pedido.notas}”</p>
            )}

            <PlazoRestante venceEn={pedido.vence_en} />
          </div>

          <div className="flex flex-col gap-2 shrink-0">
            <Button size="sm" onClick={onAprobar} disabled={guardando}>
              <Check className="w-4 h-4 mr-1" />
              Aceptar
            </Button>
            <Button
              size="sm"
              variant="secondary"
              onClick={onRechazar}
              disabled={guardando}
            >
              <X className="w-4 h-4 mr-1" />
              Rechazar
            </Button>
          </div>
        </div>
      </CardBody>
    </Card>
  )
}

/**
 * Cuánto le queda al pedido antes de vencer.
 *
 * Es el dato que ordena la cola: si no se ve, el circuito se vuelve una bandeja
 * más y los pedidos se vencen solos sin que nadie entienda por qué.
 */
function PlazoRestante({ venceEn }: { venceEn: string | null }) {
  if (!venceEn) return null

  const minutos = Math.floor((new Date(venceEn).getTime() - Date.now()) / 60000)

  if (minutos <= 0) {
    return (
      <p className="text-sm text-red-700 mt-2 flex items-center gap-1">
        <Clock className="w-3.5 h-3.5" />
        Venció. Se va a liberar el horario.
      </p>
    )
  }

  const horas = Math.floor(minutos / 60)
  const falta = horas > 0 ? `${horas} h ${minutos % 60} min` : `${minutos} min`
  // Menos de media hora es el momento en que también sale el segundo mail.
  const urgente = minutos < 30

  return (
    <p
      className={`text-sm mt-2 flex items-center gap-1 ${
        urgente ? 'text-amber-700 font-medium' : 'text-gray-500'
      }`}
    >
      <Clock className="w-3.5 h-3.5" />
      Te quedan {falta} para responder
    </p>
  )
}
