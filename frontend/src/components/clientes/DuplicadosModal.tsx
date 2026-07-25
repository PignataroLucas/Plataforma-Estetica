import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'
import { Modal, ModalHeader, ModalBody, ModalFooter, Button } from '@/components/ui'
import { getDuplicados, fusionarClientes } from '@/services/clienteService'
import type { DuplicadoGrupo, DuplicadoCliente } from '@/types/models'
import { formatDateArgentina } from '@/utils/dateUtils'

interface DuplicadosModalProps {
  isOpen: boolean
  onClose: () => void
  onMerged?: () => void
}

/** Preselecciona la ficha más completa (más datos; a igualdad, la más antigua). */
function mejorPrincipal(clientes: DuplicadoCliente[]): DuplicadoCliente {
  return [...clientes].sort((a, b) => {
    const da = a.historial_count + a.turnos_count
    const db = b.historial_count + b.turnos_count
    if (db !== da) return db - da
    return new Date(a.creado_en).getTime() - new Date(b.creado_en).getTime()
  })[0]
}

export default function DuplicadosModal({ isOpen, onClose, onMerged }: DuplicadosModalProps) {
  const [grupos, setGrupos] = useState<DuplicadoGrupo[]>([])
  const [loading, setLoading] = useState(false)
  const [principales, setPrincipales] = useState<Record<number, number>>({})
  const [confirmando, setConfirmando] = useState<number | null>(null)
  const [merging, setMerging] = useState<number | null>(null)

  useEffect(() => {
    if (isOpen) load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen])

  const load = async () => {
    setLoading(true)
    try {
      const data = await getDuplicados()
      setGrupos(data.grupos)
      const defaults: Record<number, number> = {}
      data.grupos.forEach((g, i) => {
        defaults[i] = mejorPrincipal(g.clientes).id
      })
      setPrincipales(defaults)
      setConfirmando(null)
    } catch {
      toast.error('No se pudieron cargar los duplicados')
    } finally {
      setLoading(false)
    }
  }

  const handleFusionar = async (idx: number) => {
    const grupo = grupos[idx]
    const principalId = principales[idx]
    const duplicados = grupo.clientes.filter((c) => c.id !== principalId).map((c) => c.id)
    if (duplicados.length === 0) return

    setMerging(idx)
    try {
      await fusionarClientes(principalId, duplicados)
      toast.success('Fichas fusionadas')
      await load()
      onMerged?.()
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'No se pudo fusionar')
    } finally {
      setMerging(null)
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl" showCloseButton>
      <ModalHeader>
        <h2 className="text-xl font-bold text-gray-900">Fichas duplicadas</h2>
      </ModalHeader>

      <ModalBody>
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
          </div>
        ) : grupos.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-700 font-medium">No se encontraron duplicados 🎉</p>
            <p className="text-sm text-gray-400 mt-1">
              Las fichas del centro no comparten teléfono ni email.
            </p>
          </div>
        ) : (
          <div className="space-y-5">
            <p className="text-sm text-gray-500">
              Elegí la ficha que se <strong>conserva</strong> (viene preseleccionada la más completa).
              Las demás se fusionan dentro: se les reasigna historial, turnos, rutinas y cuenta de app.{' '}
              <strong className="text-red-600">Es irreversible.</strong>
            </p>

            {grupos.map((grupo, idx) => {
              const alta = grupo.confianza === 'ALTA'
              const principalId = principales[idx]
              return (
                <div key={idx} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2 flex-wrap">
                    <span
                      className={`px-2 py-1 text-xs font-semibold rounded ${
                        alta ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {alta ? 'Coincidencia exacta' : 'Revisar'}
                    </span>
                    <span className="text-xs text-gray-500">
                      Coinciden por {grupo.clave === 'telefono' ? 'teléfono' : 'email'}:{' '}
                      <strong>{grupo.valor}</strong>
                    </span>
                  </div>

                  {!alta && (
                    <p className="text-xs text-yellow-700 mb-3">
                      Solo coincide el {grupo.clave === 'telefono' ? 'teléfono' : 'email'} — podrían ser
                      personas distintas (ej: familiares que comparten número). Revisá antes de fusionar.
                    </p>
                  )}

                  <div className="space-y-2">
                    {grupo.clientes.map((c) => {
                      const esPrincipal = c.id === principalId
                      return (
                        <label
                          key={c.id}
                          className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer ${
                            esPrincipal ? 'border-green-400 bg-green-50' : 'border-gray-200 hover:bg-gray-50'
                          }`}
                        >
                          <input
                            type="radio"
                            name={`principal-${idx}`}
                            checked={esPrincipal}
                            onChange={() => setPrincipales((p) => ({ ...p, [idx]: c.id }))}
                            className="mt-1"
                          />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="font-medium text-gray-900">{c.nombre_completo}</span>
                              {esPrincipal && (
                                <span className="text-xs text-green-700 font-medium">✓ se conserva</span>
                              )}
                              {!c.activo && <span className="text-xs text-gray-400">(inactiva)</span>}
                              {c.tiene_cuenta_app && (
                                <span className="text-xs px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded">
                                  cuenta app
                                </span>
                              )}
                            </div>
                            <div className="text-xs text-gray-500 mt-0.5">
                              {c.telefono || 'sin teléfono'} · {c.email || 'sin email'}
                            </div>
                            <div className="text-xs text-gray-400 mt-0.5">
                              {c.turnos_count} turnos · {c.historial_count} en historial · creada{' '}
                              {formatDateArgentina(c.creado_en)}
                            </div>
                          </div>
                        </label>
                      )
                    })}
                  </div>

                  <div className="mt-3 flex justify-end">
                    {confirmando === idx ? (
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-600">
                          Fusionar {grupo.clientes.length - 1} ficha(s) en la elegida. ¿Confirmás?
                        </span>
                        <Button
                          variant="ghost"
                          onClick={() => setConfirmando(null)}
                          disabled={merging === idx}
                        >
                          Cancelar
                        </Button>
                        <Button
                          variant="danger"
                          onClick={() => handleFusionar(idx)}
                          loading={merging === idx}
                        >
                          Sí, fusionar
                        </Button>
                      </div>
                    ) : (
                      <Button
                        variant={alta ? 'primary' : 'secondary'}
                        onClick={() => setConfirmando(idx)}
                      >
                        Fusionar
                      </Button>
                    )}
                  </div>
                </div>
              )
            })}
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
