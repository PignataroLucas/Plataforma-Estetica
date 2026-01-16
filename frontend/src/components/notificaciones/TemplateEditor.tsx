import { useState, useEffect } from 'react'
import { mensajesTemplatesApi } from '@/services/api'
import type { MensajeTemplate, TipoMensaje } from '@/types/models'
import Card from '@/components/ui/Card/Card'
import Button from '@/components/ui/Button/Button'
import './TemplateEditor.css'

interface Props {
  tipo: TipoMensaje
  onSaved: () => void
  onCancel: () => void
}

const TIPO_LABELS: Record<TipoMensaje, string> = {
  CONFIRMACION: 'Confirmación de Turno',
  RECORDATORIO_24H: 'Recordatorio 24 horas antes',
  RECORDATORIO_2H: 'Recordatorio 2 horas antes',
  CANCELACION: 'Cancelación de Turno',
  MODIFICACION: 'Modificación de Turno',
  PROMOCION: 'Mensaje Promocional',
}

export default function TemplateEditor({ tipo, onSaved, onCancel }: Props) {
  const [template, setTemplate] = useState<MensajeTemplate | null>(null)
  const [mensaje, setMensaje] = useState('')
  const [activo, setActivo] = useState(true)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadTemplate()
  }, [tipo])

  const loadTemplate = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await mensajesTemplatesApi.list()
      const found = response.data.find((t) => t.tipo === tipo)

      if (found) {
        const detailResponse = await mensajesTemplatesApi.get(found.id)
        setTemplate(detailResponse.data)
        setMensaje(detailResponse.data.mensaje)
        setActivo(detailResponse.data.activo)
      } else {
        // No existe template, mostrar en blanco para crear nuevo
        setTemplate(null)
        setMensaje('')
        setActivo(true)
      }
    } catch (error) {
      console.error('Error cargando template:', error)
      setError('Error al cargar el template')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (mensaje.trim().length < 10) {
      setError('El mensaje debe tener al menos 10 caracteres')
      return
    }

    try {
      setSaving(true)
      setError(null)

      if (template) {
        // Actualizar existente
        await mensajesTemplatesApi.update(template.id, {
          mensaje,
          activo,
        })
      } else {
        // Crear nuevo
        await mensajesTemplatesApi.create({
          tipo,
          mensaje,
          activo,
        })
      }

      onSaved()
    } catch (error: any) {
      console.error('Error guardando template:', error)
      setError(
        error.response?.data?.mensaje?.[0] ||
          error.response?.data?.error ||
          'Error al guardar el template'
      )
    } finally {
      setSaving(false)
    }
  }

  const handleResetDefault = async () => {
    if (!confirm('¿Restaurar este mensaje al valor por defecto?')) {
      return
    }

    try {
      setSaving(true)
      setError(null)
      await mensajesTemplatesApi.resetDefaults(tipo)
      loadTemplate()
    } catch (error) {
      console.error('Error restaurando default:', error)
      setError('Error al restaurar el mensaje por defecto')
    } finally {
      setSaving(false)
    }
  }

  const insertVariable = (variable: string) => {
    // Insertar variable en la posición del cursor
    setMensaje((prev) => prev + variable)
  }

  if (loading) {
    return (
      <Card className="template-editor">
        <h2>Cargando...</h2>
      </Card>
    )
  }

  return (
    <Card className="template-editor">
      <div className="editor-header">
        <h2>✏️ {TIPO_LABELS[tipo]}</h2>
        <button className="close-button" onClick={onCancel} title="Cerrar">
          ✕
        </button>
      </div>

      {error && (
        <div className="error-message">
          <span>⚠️ {error}</span>
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}

      <div className="form-group">
        <label htmlFor="mensaje">Mensaje</label>
        <textarea
          id="mensaje"
          value={mensaje}
          onChange={(e) => setMensaje(e.target.value)}
          rows={12}
          placeholder="Escribe tu mensaje aquí. Usa variables como {nombre_cliente}, {fecha}, {hora}..."
          className={error ? 'error' : ''}
        />
        <small className="char-count">
          {mensaje.length} caracteres
          {mensaje.length > 1600 && <span className="warning"> (máximo 1600 para WhatsApp)</span>}
        </small>
      </div>

      <div className="variables-quick-insert">
        <p className="insert-label">Insertar variable rápida:</p>
        <div className="variables-buttons">
          <button
            type="button"
            className="var-button"
            onClick={() => insertVariable('{nombre_cliente}')}
          >
            Nombre
          </button>
          <button type="button" className="var-button" onClick={() => insertVariable('{fecha}')}>
            Fecha
          </button>
          <button type="button" className="var-button" onClick={() => insertVariable('{hora}')}>
            Hora
          </button>
          <button
            type="button"
            className="var-button"
            onClick={() => insertVariable('{servicio}')}
          >
            Servicio
          </button>
          <button
            type="button"
            className="var-button"
            onClick={() => insertVariable('{profesional}')}
          >
            Profesional
          </button>
          <button
            type="button"
            className="var-button"
            onClick={() => insertVariable('{sucursal_nombre}')}
          >
            Sucursal
          </button>
        </div>
      </div>

      <div className="form-group checkbox-group">
        <label>
          <input type="checkbox" checked={activo} onChange={(e) => setActivo(e.target.checked)} />
          <span>Mensaje activo</span>
        </label>
        <small>Si está inactivo, se usará el mensaje por defecto</small>
      </div>

      <div className="editor-actions">
        <div className="left-actions">
          <Button variant="secondary" onClick={handleResetDefault} disabled={saving}>
            🔄 Restaurar por defecto
          </Button>
        </div>
        <div className="right-actions">
          <Button variant="secondary" onClick={onCancel} disabled={saving}>
            Cancelar
          </Button>
          <Button variant="primary" onClick={handleSave} disabled={saving}>
            {saving ? 'Guardando...' : 'Guardar'}
          </Button>
        </div>
      </div>
    </Card>
  )
}
