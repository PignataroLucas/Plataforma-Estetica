import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import {
  Button,
  Input,
  Modal,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Select,
} from '@/components/ui'
import { getMotivosDeRechazo } from '@/services/pedidosService'
import type { PedidoPendiente } from '@/services/pedidosService'

interface Props {
  pedido: PedidoPendiente
  onCancelar: () => void
  onConfirmar: (motivo: string, detalle: string) => void
  guardando: boolean
}

/**
 * Pide el motivo antes de rechazar un pedido.
 *
 * **El motivo es una lista y no texto libre**, y no es por comodidad: con texto
 * libre el reporte de rechazos no se puede agrupar, y esa es la métrica más útil
 * de todo el circuito — dice si la disponibilidad que publica la app se parece a
 * la realidad del centro (APROBACION_TURNOS_SPEC.md §2.4).
 *
 * Las opciones vienen del backend y no de una constante acá: el día que se
 * agregue un motivo, aparece solo.
 */
export default function RechazarPedidoModal({
  pedido,
  onCancelar,
  onConfirmar,
  guardando,
}: Props) {
  const [motivo, setMotivo] = useState('')
  const [detalle, setDetalle] = useState('')

  const { data: motivos = [] } = useQuery({
    queryKey: ['motivos-rechazo'],
    queryFn: getMotivosDeRechazo,
    // Son choices de un modelo: no cambian entre sesiones.
    staleTime: Infinity,
  })

  return (
    <Modal isOpen onClose={onCancelar}>
      <ModalHeader>Rechazar el pedido de {pedido.cliente_nombre}</ModalHeader>

      <ModalBody>
        <p className="text-sm text-gray-600 mb-4">
          A la clienta le va a llegar un aviso para que elija otro horario.{' '}
          <strong>El motivo no se le muestra</strong>: queda registrado acá.
        </p>

        <Select
          label="Motivo"
          placeholder="Elegí un motivo"
          value={motivo}
          onChange={(e) => setMotivo(e.target.value)}
          options={motivos.map((m) => ({ value: m.valor, label: m.etiqueta }))}
        />

        <div className="mt-4">
          <Input
            label="Aclaración (opcional)"
            placeholder="Para acordarte después"
            value={detalle}
            maxLength={300}
            onChange={(e) => setDetalle(e.target.value)}
          />
        </div>
      </ModalBody>

      <ModalFooter>
        <Button variant="secondary" onClick={onCancelar} disabled={guardando}>
          Volver
        </Button>
        <Button
          variant="danger"
          // Sin motivo no se puede rechazar, igual que en el backend: si la
          // validación viviera en un solo lado, el otro terminaría aceptando
          // vacíos.
          disabled={!motivo || guardando}
          onClick={() => onConfirmar(motivo, detalle)}
        >
          {guardando ? 'Rechazando…' : 'Rechazar'}
        </Button>
      </ModalFooter>
    </Modal>
  )
}
