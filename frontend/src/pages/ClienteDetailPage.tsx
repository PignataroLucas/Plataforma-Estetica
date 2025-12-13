import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Cliente } from '@/types/models'
import { getCliente } from '@/services/clienteService'
import { Button, Card, CardHeader, CardBody } from '@/components/ui'
import NotasCliente from '@/components/clientes/NotasCliente'
import PlanesTratamiento from '@/components/clientes/PlanesTratamiento'
import RutinasCuidado from '@/components/clientes/RutinasCuidado'
import ClientAnalyticsTab from '@/components/analytics/client/ClientAnalyticsTab'
import { formatDateArgentina } from '@/utils/dateUtils'

type Tab = 'overview' | 'planes' | 'rutinas' | 'notas' | 'analytics'

export default function ClienteDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [cliente, setCliente] = useState<Cliente | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<Tab>('overview')

  useEffect(() => {
    if (id) {
      loadCliente(parseInt(id))
    }
  }, [id])

  const loadCliente = async (clienteId: number) => {
    try {
      setLoading(true)
      const data = await getCliente(clienteId)
      setCliente(data)
    } catch (error) {
      console.error('Error loading client:', error)
      alert('Error al cargar el cliente')
      navigate('/clientes')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!cliente) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Cliente no encontrado</p>
        <Button onClick={() => navigate('/clientes')} variant="primary" className="mt-4">
          Volver a Clientes
        </Button>
      </div>
    )
  }

  const tabs = [
    { id: 'overview', label: 'Resumen', icon: '👤' },
    { id: 'planes', label: 'Planes de Tratamiento', icon: '📋' },
    { id: 'rutinas', label: 'Rutinas de Cuidado', icon: '🧴' },
    { id: 'notas', label: 'Notas', icon: '📝' },
    { id: 'analytics', label: 'Analytics', icon: '📊' },
  ]

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-4 mb-4">
          <Button
            variant="secondary"
            onClick={() => navigate('/clientes')}
          >
            ← Volver
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              {cliente.nombre} {cliente.apellido}
            </h1>
            <p className="text-gray-600 mt-1">
              {cliente.telefono} {cliente.email && `• ${cliente.email}`}
            </p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex -mb-px space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as Tab)}
              className={`
                py-4 px-1 border-b-2 font-medium text-sm transition-colors
                ${
                  activeTab === tab.id
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Información Personal */}
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold">Información Personal</h3>
              </CardHeader>
              <CardBody>
                <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Nombre Completo</dt>
                    <dd className="text-sm text-gray-900">{cliente.nombre} {cliente.apellido}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Email</dt>
                    <dd className="text-sm text-gray-900">{cliente.email || '-'}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Teléfono</dt>
                    <dd className="text-sm text-gray-900">{cliente.telefono}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Fecha de Nacimiento</dt>
                    <dd className="text-sm text-gray-900">
                      {cliente.fecha_nacimiento ? formatDateArgentina(cliente.fecha_nacimiento) : '-'}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Dirección</dt>
                    <dd className="text-sm text-gray-900">
                      {cliente.direccion || '-'}
                      {cliente.ciudad && `, ${cliente.ciudad}`}
                      {cliente.provincia && `, ${cliente.provincia}`}
                    </dd>
                  </div>
                </dl>
              </CardBody>
            </Card>

            {/* Datos del Paciente */}
            {(cliente.motivo_consulta || cliente.objetivo_principal) && (
              <Card>
                <CardHeader>
                  <h3 className="text-lg font-semibold">Datos del Paciente</h3>
                </CardHeader>
                <CardBody>
                  <dl className="space-y-4">
                    {cliente.motivo_consulta && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Motivo de Consulta</dt>
                        <dd className="text-sm text-gray-900 mt-1 whitespace-pre-wrap">
                          {cliente.motivo_consulta}
                        </dd>
                      </div>
                    )}
                    {cliente.objetivo_principal && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Objetivo Principal</dt>
                        <dd className="text-sm text-gray-900 mt-1">{cliente.objetivo_principal}</dd>
                      </div>
                    )}
                  </dl>
                </CardBody>
              </Card>
            )}

            {/* Historia Clínica */}
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold">Historia Clínica</h3>
              </CardHeader>
              <CardBody>
                <div className="space-y-4">
                  {/* Contraindicaciones */}
                  {(cliente.embarazo_lactancia || cliente.marcapasos_implantes ||
                    cliente.cancer_historial || cliente.herpes_historial) && (
                    <div>
                      <dt className="text-sm font-medium text-gray-700 mb-2">Contraindicaciones:</dt>
                      <dd className="space-y-1">
                        {cliente.embarazo_lactancia && (
                          <span className="inline-block px-2 py-1 text-xs bg-red-100 text-red-800 rounded mr-2">
                            Embarazo/Lactancia
                          </span>
                        )}
                        {cliente.marcapasos_implantes && (
                          <span className="inline-block px-2 py-1 text-xs bg-red-100 text-red-800 rounded mr-2">
                            Marcapasos/Implantes
                          </span>
                        )}
                        {cliente.cancer_historial && (
                          <span className="inline-block px-2 py-1 text-xs bg-red-100 text-red-800 rounded mr-2">
                            Cáncer
                          </span>
                        )}
                        {cliente.herpes_historial && (
                          <span className="inline-block px-2 py-1 text-xs bg-red-100 text-red-800 rounded mr-2">
                            Herpes
                          </span>
                        )}
                      </dd>
                    </div>
                  )}

                  {/* Alergias */}
                  {cliente.tiene_alergias && cliente.alergias && (
                    <div>
                      <dt className="text-sm font-medium text-gray-700">Alergias</dt>
                      <dd className="text-sm text-gray-900 mt-1">{cliente.alergias}</dd>
                    </div>
                  )}

                  {/* Medicación */}
                  {cliente.medicacion_actual && cliente.medicacion_detalle && (
                    <div>
                      <dt className="text-sm font-medium text-gray-700">Medicación Actual</dt>
                      <dd className="text-sm text-gray-900 mt-1">{cliente.medicacion_detalle}</dd>
                    </div>
                  )}

                  {/* Notas médicas */}
                  {cliente.notas_medicas && (
                    <div>
                      <dt className="text-sm font-medium text-gray-700">Notas Médicas</dt>
                      <dd className="text-sm text-gray-900 mt-1 whitespace-pre-wrap">
                        {cliente.notas_medicas}
                      </dd>
                    </div>
                  )}
                </div>
              </CardBody>
            </Card>

            {/* Evaluación Facial */}
            {(cliente.tipo_piel || cliente.diagnostico_facial) && (
              <Card>
                <CardHeader>
                  <h3 className="text-lg font-semibold">Evaluación Facial</h3>
                </CardHeader>
                <CardBody>
                  <dl className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {cliente.tipo_piel && (
                      <div>
                        <dt className="text-xs font-medium text-gray-500">Tipo de Piel</dt>
                        <dd className="text-sm text-gray-900">{cliente.tipo_piel}</dd>
                      </div>
                    )}
                    {cliente.poros && (
                      <div>
                        <dt className="text-xs font-medium text-gray-500">Poros</dt>
                        <dd className="text-sm text-gray-900">{cliente.poros}</dd>
                      </div>
                    )}
                    {cliente.brillo && (
                      <div>
                        <dt className="text-xs font-medium text-gray-500">Brillo</dt>
                        <dd className="text-sm text-gray-900">{cliente.brillo}</dd>
                      </div>
                    )}
                    {cliente.textura && (
                      <div>
                        <dt className="text-xs font-medium text-gray-500">Textura</dt>
                        <dd className="text-sm text-gray-900">{cliente.textura}</dd>
                      </div>
                    )}
                  </dl>
                  {cliente.diagnostico_facial && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <dt className="text-sm font-medium text-gray-700">Diagnóstico</dt>
                      <dd className="text-sm text-gray-900 mt-1 whitespace-pre-wrap">
                        {cliente.diagnostico_facial}
                      </dd>
                    </div>
                  )}
                </CardBody>
              </Card>
            )}

            {/* Evaluación Corporal */}
            {(cliente.celulitis_grado !== undefined || cliente.diagnostico_corporal) && (
              <Card>
                <CardHeader>
                  <h3 className="text-lg font-semibold">Evaluación Corporal</h3>
                </CardHeader>
                <CardBody>
                  <dl className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {cliente.celulitis_grado !== undefined && (
                      <div>
                        <dt className="text-xs font-medium text-gray-500">Celulitis</dt>
                        <dd className="text-sm text-gray-900">Grado {cliente.celulitis_grado}</dd>
                      </div>
                    )}
                    {cliente.adiposidad && (
                      <div>
                        <dt className="text-xs font-medium text-gray-500">Adiposidad</dt>
                        <dd className="text-sm text-gray-900">{cliente.adiposidad}</dd>
                      </div>
                    )}
                    {cliente.flacidez && (
                      <div>
                        <dt className="text-xs font-medium text-gray-500">Flacidez</dt>
                        <dd className="text-sm text-gray-900">{cliente.flacidez}</dd>
                      </div>
                    )}
                    {cliente.estrias && (
                      <div>
                        <dt className="text-xs font-medium text-gray-500">Estrías</dt>
                        <dd className="text-sm text-gray-900">{cliente.estrias}</dd>
                      </div>
                    )}
                  </dl>
                  {cliente.diagnostico_corporal && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <dt className="text-sm font-medium text-gray-700">Diagnóstico</dt>
                      <dd className="text-sm text-gray-900 mt-1 whitespace-pre-wrap">
                        {cliente.diagnostico_corporal}
                      </dd>
                    </div>
                  )}
                </CardBody>
              </Card>
            )}
          </div>
        )}

        {activeTab === 'planes' && (
          <Card>
            <CardBody>
              <PlanesTratamiento clienteId={cliente.id} />
            </CardBody>
          </Card>
        )}

        {activeTab === 'rutinas' && (
          <Card>
            <CardBody>
              <RutinasCuidado clienteId={cliente.id} />
            </CardBody>
          </Card>
        )}

        {activeTab === 'notas' && (
          <Card>
            <CardBody>
              <NotasCliente clienteId={cliente.id} />
            </CardBody>
          </Card>
        )}

        {activeTab === 'analytics' && (
          <ClientAnalyticsTab clienteId={cliente.id} />
        )}
      </div>
    </div>
  )
}
