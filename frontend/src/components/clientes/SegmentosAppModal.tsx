import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'
import { Modal, ModalHeader, ModalBody, ModalFooter, Button, Input } from '@/components/ui'
import {
  getSegmentosApp,
  createSegmentoApp,
  updateSegmentoApp,
  deleteSegmentoApp,
} from '@/services/clienteService'
import type { SegmentoApp } from '@/types/models'

interface SegmentosAppModalProps {
  isOpen: boolean
  onClose: () => void
  /** El descuento de una ficha puede haber cambiado: la lista se recarga. */
  onCambios?: () => void
}

/**
 * ABM de segmentos de la app.
 *
 * El descuento de la app se maneja acá y no ficha por ficha: el día que VIP
 * pase de 15% a 20% se edita un registro (COMPRA_EN_APP_SPEC.md §5.8). Lo que
 * se guarda acá es lo que la clienta ve en la app y lo que va a pagar.
 */
export default function SegmentosAppModal({ isOpen, onClose, onCambios }: SegmentosAppModalProps) {
  const [segmentos, setSegmentos] = useState<SegmentoApp[]>([])
  const [loading, setLoading] = useState(false)
  const [guardando, setGuardando] = useState<number | 'nuevo' | null>(null)
  const [confirmando, setConfirmando] = useState<number | null>(null)
  const [nuevo, setNuevo] = useState({ nombre: '', porcentaje: '' })

  useEffect(() => {
    if (isOpen) load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen])

  const load = async () => {
    setLoading(true)
    try {
      const data = await getSegmentosApp()
      setSegmentos(data.results)
      setConfirmando(null)
    } catch {
      toast.error('No se pudieron cargar los segmentos')
    } finally {
      setLoading(false)
    }
  }

  const handleGuardarPorcentaje = async (segmento: SegmentoApp, valor: string) => {
    if (valor === segmento.porcentaje_descuento) return

    setGuardando(segmento.id)
    try {
      await updateSegmentoApp(segmento.id, { porcentaje_descuento: valor })
      toast.success(`${segmento.nombre}: ${valor}%`)
      await load()
      onCambios?.()
    } catch {
      toast.error('No se pudo guardar el descuento')
      await load()
    } finally {
      setGuardando(null)
    }
  }

  const handleCrear = async () => {
    const nombre = nuevo.nombre.trim()
    if (!nombre) return

    setGuardando('nuevo')
    try {
      await createSegmentoApp({
        nombre,
        porcentaje_descuento: nuevo.porcentaje || '0',
      })
      setNuevo({ nombre: '', porcentaje: '' })
      await load()
      onCambios?.()
    } catch {
      toast.error('No se pudo crear el segmento')
    } finally {
      setGuardando(null)
    }
  }

  const handleEliminar = async (segmento: SegmentoApp) => {
    try {
      await deleteSegmentoApp(segmento.id)
      toast.success('Segmento eliminado')
      await load()
      onCambios?.()
    } catch {
      // El general no se puede borrar: el backend lo rechaza con 400.
      toast.error('No se pudo eliminar. El segmento general no se elimina: ponelo en 0%.')
      setConfirmando(null)
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="md" showCloseButton>
      <ModalHeader>
        <h2 className="text-xl font-bold text-gray-900">Segmentos de la app</h2>
      </ModalHeader>

      <ModalBody>
        <p className="text-sm text-gray-600 mb-4">
          El descuento que cada clienta ve en la app y paga al comprar. Sin segmento
          propio le corresponde el general.
        </p>

        {loading ? (
          <p className="text-sm text-gray-500">Cargando…</p>
        ) : (
          <div className="space-y-3">
            {segmentos.map((segmento) => (
              <div
                key={segmento.id}
                className="flex items-center gap-3 border border-gray-200 rounded-lg p-3"
              >
                <div className="flex-1">
                  <p className="font-medium text-gray-900">
                    {segmento.nombre}
                    {segmento.es_predeterminado && (
                      <span className="ml-2 text-xs font-normal text-gray-500">general</span>
                    )}
                  </p>
                  <p className="text-xs text-gray-500">
                    {segmento.es_predeterminado
                      ? 'Toda clienta sin segmento propio'
                      : `${segmento.cantidad_clientes} clienta${segmento.cantidad_clientes === 1 ? '' : 's'}`}
                  </p>
                </div>

                <div className="w-24">
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    step="0.5"
                    defaultValue={segmento.porcentaje_descuento}
                    disabled={guardando === segmento.id}
                    // Se guarda al salir del campo: es un número suelto, no vale
                    // un formulario con botón para cada fila.
                    onBlur={(e) => handleGuardarPorcentaje(segmento, e.target.value)}
                  />
                </div>
                <span className="text-sm text-gray-500">%</span>

                {segmento.es_predeterminado ? (
                  <span className="w-20" />
                ) : confirmando === segmento.id ? (
                  <Button variant="danger" size="sm" onClick={() => handleEliminar(segmento)}>
                    Confirmar
                  </Button>
                ) : (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => setConfirmando(segmento.id)}
                  >
                    Eliminar
                  </Button>
                )}
              </div>
            ))}

            <div className="flex items-end gap-3 border-t border-gray-200 pt-4">
              <div className="flex-1">
                <Input
                  label="Nuevo segmento"
                  placeholder="VIP"
                  value={nuevo.nombre}
                  onChange={(e) => setNuevo((p) => ({ ...p, nombre: e.target.value }))}
                  fullWidth
                />
              </div>
              <div className="w-24">
                <Input
                  label="%"
                  type="number"
                  min="0"
                  max="100"
                  step="0.5"
                  value={nuevo.porcentaje}
                  onChange={(e) => setNuevo((p) => ({ ...p, porcentaje: e.target.value }))}
                />
              </div>
              <Button
                variant="primary"
                onClick={handleCrear}
                loading={guardando === 'nuevo'}
                disabled={!nuevo.nombre.trim()}
              >
                Agregar
              </Button>
            </div>
          </div>
        )}
      </ModalBody>

      <ModalFooter>
        <Button variant="secondary" onClick={onClose}>
          Cerrar
        </Button>
      </ModalFooter>
    </Modal>
  )
}
