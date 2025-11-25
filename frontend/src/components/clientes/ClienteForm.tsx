import { useState, FormEvent, ChangeEvent, useEffect } from 'react'
import { Cliente } from '@/types/models'
import { Button, Input, Select, DateInput } from '@/components/ui'

/**
 * ClienteForm - Formulario de Cliente con sistema de tracking completo
 * Incluye: Datos personales, historia clínica, evaluación facial y corporal
 */

interface ClienteFormProps {
  cliente?: Cliente | null
  onSubmit: (data: Partial<Cliente>) => Promise<void>
  onCancel: () => void
  loading?: boolean
  formId?: string
  showButtons?: boolean
}

export default function ClienteForm({
  cliente,
  onSubmit,
  onCancel,
  loading = false,
  formId = 'cliente-form',
  showButtons = true,
}: ClienteFormProps) {
  const [formData, setFormData] = useState<Partial<Cliente>>({
    nombre: '',
    apellido: '',
    email: '',
    telefono: '',
    telefono_alternativo: '',
    fecha_nacimiento: '',
    direccion: '',
    ciudad: '',
    provincia: '',
    codigo_postal: '',
    motivo_consulta: '',
    objetivo_principal: '',
    embarazo_lactancia: false,
    marcapasos_implantes: false,
    cancer_historial: false,
    herpes_historial: false,
    alergias: '',
    tiene_alergias: false,
    medicacion_actual: false,
    medicacion_detalle: '',
    tratamientos_previos: false,
    tratamientos_previos_detalle: '',
    tatuajes_zona_tratamiento: false,
    tatuajes_zonas: '',
    contraindicaciones: '',
    notas_medicas: '',
    detalle_general: '',
    tipo_piel: undefined,
    poros: undefined,
    brillo: undefined,
    textura: undefined,
    estado_piel: '',
    observaciones_faciales: '',
    diagnostico_facial: '',
    zonas_tratar: '',
    celulitis_grado: undefined,
    celulitis_tipo: undefined,
    adiposidad: undefined,
    flacidez: undefined,
    estrias: undefined,
    retencion_liquidos: false,
    observaciones_corporales: '',
    diagnostico_corporal: '',
    preferencias: '',
    acepta_promociones: true,
    acepta_whatsapp: true,
  })

  const [errors, setErrors] = useState<Partial<Record<keyof Cliente, string>>>({})
  const [expandedSections, setExpandedSections] = useState({
    personal: true,
    contacto: true,
    tracking: false,
    historia: false,
    facial: false,
    corporal: false,
    preferencias: false,
  })

  // Cargar datos del cliente si estamos editando
  useEffect(() => {
    if (cliente) {
      setFormData({
        nombre: cliente.nombre,
        apellido: cliente.apellido,
        email: cliente.email,
        telefono: cliente.telefono,
        telefono_alternativo: cliente.telefono_alternativo,
        fecha_nacimiento: cliente.fecha_nacimiento,
        direccion: cliente.direccion,
        ciudad: cliente.ciudad,
        provincia: cliente.provincia,
        codigo_postal: cliente.codigo_postal,
        motivo_consulta: cliente.motivo_consulta,
        objetivo_principal: cliente.objetivo_principal,
        embarazo_lactancia: cliente.embarazo_lactancia,
        marcapasos_implantes: cliente.marcapasos_implantes,
        cancer_historial: cliente.cancer_historial,
        herpes_historial: cliente.herpes_historial,
        alergias: cliente.alergias,
        tiene_alergias: cliente.tiene_alergias,
        medicacion_actual: cliente.medicacion_actual,
        medicacion_detalle: cliente.medicacion_detalle,
        tratamientos_previos: cliente.tratamientos_previos,
        tratamientos_previos_detalle: cliente.tratamientos_previos_detalle,
        tatuajes_zona_tratamiento: cliente.tatuajes_zona_tratamiento,
        tatuajes_zonas: cliente.tatuajes_zonas,
        contraindicaciones: cliente.contraindicaciones,
        notas_medicas: cliente.notas_medicas,
        detalle_general: cliente.detalle_general,
        tipo_piel: cliente.tipo_piel,
        poros: cliente.poros,
        brillo: cliente.brillo,
        textura: cliente.textura,
        estado_piel: cliente.estado_piel,
        observaciones_faciales: cliente.observaciones_faciales,
        diagnostico_facial: cliente.diagnostico_facial,
        zonas_tratar: cliente.zonas_tratar,
        celulitis_grado: cliente.celulitis_grado,
        celulitis_tipo: cliente.celulitis_tipo,
        adiposidad: cliente.adiposidad,
        flacidez: cliente.flacidez,
        estrias: cliente.estrias,
        retencion_liquidos: cliente.retencion_liquidos,
        observaciones_corporales: cliente.observaciones_corporales,
        diagnostico_corporal: cliente.diagnostico_corporal,
        preferencias: cliente.preferencias,
        acepta_promociones: cliente.acepta_promociones,
        acepta_whatsapp: cliente.acepta_whatsapp,
      })
    }
  }, [cliente])

  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof Cliente, string>> = {}

    if (!formData.nombre?.trim()) {
      newErrors.nombre = 'El nombre es requerido'
    }

    if (!formData.apellido?.trim()) {
      newErrors.apellido = 'El apellido es requerido'
    }

    if (formData.email?.trim() && !/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email inválido'
    }

    if (!formData.telefono?.trim()) {
      newErrors.telefono = 'El teléfono es requerido'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    await onSubmit(formData)
  }

  const handleChange = (e: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target
    const checked = (e.target as HTMLInputElement).checked

    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }))

    if (errors[name as keyof Cliente]) {
      setErrors(prev => ({
        ...prev,
        [name]: undefined,
      }))
    }
  }

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section],
    }))
  }

  return (
    <form id={formId} onSubmit={handleSubmit} className="space-y-6">
      {/* Datos Personales */}
      <div className="border border-gray-200 rounded-lg">
        <button
          type="button"
          onClick={() => toggleSection('personal')}
          className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
        >
          <h3 className="text-lg font-semibold text-gray-900">
            Datos Personales
          </h3>
          <span className="text-gray-500">
            {expandedSections.personal ? '−' : '+'}
          </span>
        </button>
        {expandedSections.personal && (
          <div className="p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Nombre"
                name="nombre"
                value={formData.nombre}
                onChange={handleChange}
                error={errors.nombre}
                required
                fullWidth
              />

              <Input
                label="Apellido"
                name="apellido"
                value={formData.apellido}
                onChange={handleChange}
                error={errors.apellido}
                required
                fullWidth
              />

              <Input
                label="Email"
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                error={errors.email}
                fullWidth
                placeholder="correo@ejemplo.com"
              />

              <DateInput
                label="Fecha de Nacimiento"
                value={formData.fecha_nacimiento || ''}
                onChange={(value) => setFormData(prev => ({ ...prev, fecha_nacimiento: value }))}
              />
            </div>
          </div>
        )}
      </div>

      {/* Información de Contacto */}
      <div className="border border-gray-200 rounded-lg">
        <button
          type="button"
          onClick={() => toggleSection('contacto')}
          className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
        >
          <h3 className="text-lg font-semibold text-gray-900">
            Información de Contacto
          </h3>
          <span className="text-gray-500">
            {expandedSections.contacto ? '−' : '+'}
          </span>
        </button>
        {expandedSections.contacto && (
          <div className="p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Teléfono Principal"
                name="telefono"
                value={formData.telefono}
                onChange={handleChange}
                error={errors.telefono}
                required
                fullWidth
                placeholder="ej: +54 9 11 1234-5678"
              />

              <Input
                label="Teléfono Alternativo"
                name="telefono_alternativo"
                value={formData.telefono_alternativo}
                onChange={handleChange}
                fullWidth
                placeholder="Opcional"
              />

              <Input
                label="Dirección"
                name="direccion"
                value={formData.direccion}
                onChange={handleChange}
                fullWidth
                className="md:col-span-2"
              />

              <Input
                label="Ciudad"
                name="ciudad"
                value={formData.ciudad}
                onChange={handleChange}
                fullWidth
              />

              <Input
                label="Provincia"
                name="provincia"
                value={formData.provincia}
                onChange={handleChange}
                fullWidth
              />

              <Input
                label="Código Postal"
                name="codigo_postal"
                value={formData.codigo_postal}
                onChange={handleChange}
                fullWidth
              />
            </div>
          </div>
        )}
      </div>

      {/* A) Datos del Paciente (Tracking) */}
      <div className="border border-gray-200 rounded-lg">
        <button
          type="button"
          onClick={() => toggleSection('tracking')}
          className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
        >
          <h3 className="text-lg font-semibold text-gray-900">
            A) Datos del Paciente (Tracking)
          </h3>
          <span className="text-gray-500">
            {expandedSections.tracking ? '−' : '+'}
          </span>
        </button>
        {expandedSections.tracking && (
          <div className="p-4 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Motivo de Consulta
              </label>
              <textarea
                name="motivo_consulta"
                value={formData.motivo_consulta}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                rows={2}
                placeholder="¿Por qué consulta el paciente?"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Objetivo Principal
              </label>
              <Input
                name="objetivo_principal"
                value={formData.objetivo_principal}
                onChange={handleChange}
                fullWidth
                placeholder="Objetivo en una frase"
              />
            </div>
          </div>
        )}
      </div>

      {/* B) Historia / Contraindicaciones */}
      <div className="border border-gray-200 rounded-lg">
        <button
          type="button"
          onClick={() => toggleSection('historia')}
          className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
        >
          <h3 className="text-lg font-semibold text-gray-900">
            B) Historia / Contraindicaciones
          </h3>
          <span className="text-gray-500">
            {expandedSections.historia ? '−' : '+'}
          </span>
        </button>
        {expandedSections.historia && (
          <div className="p-4 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="embarazo_lactancia"
                  checked={formData.embarazo_lactancia}
                  onChange={handleChange}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">
                  Embarazo / Lactancia
                </span>
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="marcapasos_implantes"
                  checked={formData.marcapasos_implantes}
                  onChange={handleChange}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">
                  Marcapasos / Implantes Metálicos
                </span>
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="cancer_historial"
                  checked={formData.cancer_historial}
                  onChange={handleChange}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">
                  Cáncer (actual o antecedente)
                </span>
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="herpes_historial"
                  checked={formData.herpes_historial}
                  onChange={handleChange}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">
                  Historial de Herpes
                </span>
              </label>
            </div>

            <div>
              <label className="flex items-center mb-2">
                <input
                  type="checkbox"
                  name="tiene_alergias"
                  checked={formData.tiene_alergias}
                  onChange={handleChange}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm font-medium text-gray-700">
                  Tiene Alergias
                </span>
              </label>
              {formData.tiene_alergias && (
                <textarea
                  name="alergias"
                  value={formData.alergias}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  rows={2}
                  placeholder="Detalle de alergias o sensibilidades"
                />
              )}
            </div>

            <div>
              <label className="flex items-center mb-2">
                <input
                  type="checkbox"
                  name="medicacion_actual"
                  checked={formData.medicacion_actual}
                  onChange={handleChange}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm font-medium text-gray-700">
                  Medicación Actual
                </span>
              </label>
              {formData.medicacion_actual && (
                <textarea
                  name="medicacion_detalle"
                  value={formData.medicacion_detalle}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  rows={2}
                  placeholder="Detalle de medicación actual"
                />
              )}
            </div>

            <div>
              <label className="flex items-center mb-2">
                <input
                  type="checkbox"
                  name="tratamientos_previos"
                  checked={formData.tratamientos_previos}
                  onChange={handleChange}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm font-medium text-gray-700">
                  Tratamientos Estéticos Previos
                </span>
              </label>
              {formData.tratamientos_previos && (
                <textarea
                  name="tratamientos_previos_detalle"
                  value={formData.tratamientos_previos_detalle}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  rows={2}
                  placeholder="Detalle de tratamientos previos"
                />
              )}
            </div>

            <div>
              <label className="flex items-center mb-2">
                <input
                  type="checkbox"
                  name="tatuajes_zona_tratamiento"
                  checked={formData.tatuajes_zona_tratamiento}
                  onChange={handleChange}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm font-medium text-gray-700">
                  Tatuajes en Zona a Tratar
                </span>
              </label>
              {formData.tatuajes_zona_tratamiento && (
                <textarea
                  name="tatuajes_zonas"
                  value={formData.tatuajes_zonas}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  rows={2}
                  placeholder="Zonas con tatuajes"
                />
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Contraindicaciones
              </label>
              <textarea
                name="contraindicaciones"
                value={formData.contraindicaciones}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                rows={2}
                placeholder="Contraindicaciones generales"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Notas Médicas
              </label>
              <textarea
                name="notas_medicas"
                value={formData.notas_medicas}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                rows={2}
                placeholder="Información médica adicional relevante"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Aclaraciones Adicionales
              </label>
              <textarea
                name="detalle_general"
                value={formData.detalle_general}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                rows={2}
                placeholder="Aclaraciones adicionales generales"
              />
            </div>
          </div>
        )}
      </div>

      {/* C) Evaluación Facial */}
      <div className="border border-gray-200 rounded-lg">
        <button
          type="button"
          onClick={() => toggleSection('facial')}
          className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
        >
          <h3 className="text-lg font-semibold text-gray-900">
            C) Evaluación Facial
          </h3>
          <span className="text-gray-500">
            {expandedSections.facial ? '−' : '+'}
          </span>
        </button>
        {expandedSections.facial && (
          <div className="p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Select
                label="Tipo de Piel"
                name="tipo_piel"
                value={formData.tipo_piel || ''}
                onChange={handleChange}
                options={[
                  { value: '', label: 'Seleccionar...' },
                  { value: 'NORMAL', label: 'Normal' },
                  { value: 'SECA', label: 'Seca' },
                  { value: 'MIXTA', label: 'Mixta' },
                  { value: 'GRASA', label: 'Grasa' },
                  { value: 'NO_DETERMINADO', label: 'No determinado' },
                ]}
              />

              <Select
                label="Poros"
                name="poros"
                value={formData.poros || ''}
                onChange={handleChange}
                options={[
                  { value: '', label: 'Seleccionar...' },
                  { value: 'FINOS', label: 'Finos' },
                  { value: 'MEDIOS', label: 'Medios' },
                  { value: 'DILATADOS', label: 'Dilatados' },
                  { value: 'MIXTO', label: 'Mixto' },
                ]}
              />

              <Select
                label="Brillo"
                name="brillo"
                value={formData.brillo || ''}
                onChange={handleChange}
                options={[
                  { value: '', label: 'Seleccionar...' },
                  { value: 'BAJO', label: 'Bajo' },
                  { value: 'MEDIO', label: 'Medio' },
                  { value: 'ALTO', label: 'Alto' },
                ]}
              />

              <Select
                label="Textura"
                name="textura"
                value={formData.textura || ''}
                onChange={handleChange}
                options={[
                  { value: '', label: 'Seleccionar...' },
                  { value: 'UNIFORME', label: 'Uniforme' },
                  { value: 'ASPERA', label: 'Áspera' },
                  { value: 'DESCAMACION', label: 'Descamación' },
                  { value: 'MIXTA', label: 'Mixta' },
                ]}
              />
            </div>

            <div className="mt-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Estado de Piel
                </label>
                <textarea
                  name="estado_piel"
                  value={formData.estado_piel}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  rows={2}
                  placeholder="Ej: deshidratada, sensible, rosácea, manchas, acné, etc."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Observaciones de Zonas Puntuales
                </label>
                <textarea
                  name="observaciones_faciales"
                  value={formData.observaciones_faciales}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  rows={2}
                  placeholder="Observaciones específicas de zonas faciales"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Diagnóstico Facial (Resumen)
                </label>
                <textarea
                  name="diagnostico_facial"
                  value={formData.diagnostico_facial}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  rows={2}
                  placeholder="Resumen del diagnóstico facial"
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* D) Evaluación Corporal */}
      <div className="border border-gray-200 rounded-lg">
        <button
          type="button"
          onClick={() => toggleSection('corporal')}
          className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
        >
          <h3 className="text-lg font-semibold text-gray-900">
            D) Evaluación Corporal
          </h3>
          <span className="text-gray-500">
            {expandedSections.corporal ? '−' : '+'}
          </span>
        </button>
        {expandedSections.corporal && (
          <div className="p-4">
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Zonas a Tratar
              </label>
              <textarea
                name="zonas_tratar"
                value={formData.zonas_tratar}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                rows={2}
                placeholder="Zonas corporales a tratar"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Select
                label="Grado de Celulitis"
                name="celulitis_grado"
                value={formData.celulitis_grado?.toString() || ''}
                onChange={handleChange}
                options={[
                  { value: '', label: 'Seleccionar...' },
                  { value: '0', label: 'Grado 0' },
                  { value: '1', label: 'Grado 1' },
                  { value: '2', label: 'Grado 2' },
                  { value: '3', label: 'Grado 3' },
                ]}
              />

              <Select
                label="Tipo de Celulitis"
                name="celulitis_tipo"
                value={formData.celulitis_tipo || ''}
                onChange={handleChange}
                options={[
                  { value: '', label: 'Seleccionar...' },
                  { value: 'EDEMATOSA', label: 'Edematosa' },
                  { value: 'FIBROSA', label: 'Fibrosa' },
                  { value: 'BLANDA', label: 'Blanda' },
                  { value: 'MIXTA', label: 'Mixta' },
                  { value: 'NO_APLICA', label: 'No aplica' },
                ]}
              />

              <Select
                label="Adiposidad Localizada"
                name="adiposidad"
                value={formData.adiposidad || ''}
                onChange={handleChange}
                options={[
                  { value: '', label: 'Seleccionar...' },
                  { value: 'BAJA', label: 'Baja' },
                  { value: 'MEDIA', label: 'Media' },
                  { value: 'ALTA', label: 'Alta' },
                  { value: 'NO_APLICA', label: 'No aplica' },
                ]}
              />

              <Select
                label="Flacidez Corporal"
                name="flacidez"
                value={formData.flacidez || ''}
                onChange={handleChange}
                options={[
                  { value: '', label: 'Seleccionar...' },
                  { value: 'LEVE', label: 'Leve' },
                  { value: 'MODERADA', label: 'Moderada' },
                  { value: 'MARCADA', label: 'Marcada' },
                  { value: 'NO_APLICA', label: 'No aplica' },
                ]}
              />

              <Select
                label="Estrías"
                name="estrias"
                value={formData.estrias || ''}
                onChange={handleChange}
                options={[
                  { value: '', label: 'Seleccionar...' },
                  { value: 'NO', label: 'No' },
                  { value: 'BLANCAS', label: 'Blancas' },
                  { value: 'ROJAS', label: 'Rojas' },
                  { value: 'MIXTAS', label: 'Mixtas' },
                ]}
              />

              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="retencion_liquidos"
                  checked={formData.retencion_liquidos}
                  onChange={handleChange}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">
                  Retención de Líquidos
                </span>
              </label>
            </div>

            <div className="mt-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Observaciones Corporales
                </label>
                <textarea
                  name="observaciones_corporales"
                  value={formData.observaciones_corporales}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  rows={2}
                  placeholder="Observaciones sobre evaluación corporal"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Diagnóstico Corporal (Resumen)
                </label>
                <textarea
                  name="diagnostico_corporal"
                  value={formData.diagnostico_corporal}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  rows={2}
                  placeholder="Resumen del diagnóstico corporal"
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Preferencias y Comunicación */}
      <div className="border border-gray-200 rounded-lg">
        <button
          type="button"
          onClick={() => toggleSection('preferencias')}
          className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
        >
          <h3 className="text-lg font-semibold text-gray-900">
            Preferencias y Comunicación
          </h3>
          <span className="text-gray-500">
            {expandedSections.preferencias ? '−' : '+'}
          </span>
        </button>
        {expandedSections.preferencias && (
          <div className="p-4 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Preferencias del Cliente
              </label>
              <textarea
                name="preferencias"
                value={formData.preferencias}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                rows={2}
                placeholder="Ej: Prefiere turnos por la mañana, aceites esenciales de lavanda..."
              />
            </div>

            <div className="space-y-3">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="acepta_promociones"
                  checked={formData.acepta_promociones}
                  onChange={handleChange}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">
                  Acepta recibir promociones y novedades
                </span>
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="acepta_whatsapp"
                  checked={formData.acepta_whatsapp}
                  onChange={handleChange}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">
                  Acepta notificaciones por WhatsApp
                </span>
              </label>
            </div>
          </div>
        )}
      </div>

      {/* Botones de Acción */}
      {showButtons && (
        <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
          <Button
            type="button"
            variant="secondary"
            onClick={onCancel}
            disabled={loading}
          >
            Cancelar
          </Button>
          <Button
            type="submit"
            variant="primary"
            loading={loading}
          >
            {cliente ? 'Actualizar Cliente' : 'Crear Cliente'}
          </Button>
        </div>
      )}
    </form>
  )
}
