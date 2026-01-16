import { useState, useEffect, useCallback } from 'react'
import { mensajesTemplatesApi } from '@/services/api'
import type { MensajeTemplateList, TipoMensaje } from '@/types/models'
import { useAuthStore } from '@/stores/authStore'
import TemplateEditor from '@/components/notificaciones/TemplateEditor'
import VariablesGuide from '@/components/notificaciones/VariablesGuide'
import Card from '@/components/ui/Card/Card'
import Button from '@/components/ui/Button/Button'
import Badge from '@/components/ui/Badge/Badge'
import './ConfiguracionWhatsAppPage.css'

const TIPO_LABELS: Record<TipoMensaje, string> = {
  CONFIRMACION: 'Confirmación de Turno',
  RECORDATORIO_24H: 'Recordatorio 24 horas antes',
  RECORDATORIO_2H: 'Recordatorio 2 horas antes',
  CANCELACION: 'Cancelación de Turno',
  MODIFICACION: 'Modificación de Turno',
  PROMOCION: 'Mensaje Promocional',
}

const TIPO_ICONS: Record<TipoMensaje, string> = {
  CONFIRMACION: '✅',
  RECORDATORIO_24H: '📅',
  RECORDATORIO_2H: '⏰',
  CANCELACION: '❌',
  MODIFICACION: '✏️',
  PROMOCION: '🎁',
}

// Lista de todos los tipos que queremos mostrar
const ALL_TIPOS: TipoMensaje[] = [
  'CONFIRMACION',
  'RECORDATORIO_24H',
  'RECORDATORIO_2H',
  'CANCELACION',
]

export default function ConfiguracionWhatsAppPage() {
  const { user } = useAuthStore()
  const [templates, setTemplates] = useState<MensajeTemplateList[]>([])
  const [selectedTipo, setSelectedTipo] = useState<TipoMensaje | null>(null)
  const [loading, setLoading] = useState(true)
  const [resetting, setResetting] = useState(false)

  const isAdmin = user?.rol === 'ADMIN'

  const loadTemplates = useCallback(async () => {
    try {
      setLoading(true)
      const response = await mensajesTemplatesApi.list()
      setTemplates(response.data)
    } catch (error) {
      console.error('Error cargando templates:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (isAdmin) {
      loadTemplates()
    }
  }, [isAdmin, loadTemplates])

  const handleTemplateUpdated = () => {
    loadTemplates()
    setSelectedTipo(null)
  }

  const handleResetAllDefaults = async () => {
    if (
      !confirm(
        '¿Restaurar TODOS los mensajes a los valores por defecto?\n\nEsto sobrescribirá todos los mensajes personalizados.'
      )
    ) {
      return
    }

    try {
      setResetting(true)
      await mensajesTemplatesApi.resetDefaults()
      loadTemplates()
      alert('✅ Todos los mensajes han sido restaurados a los valores por defecto')
    } catch (error) {
      console.error('Error restaurando defaults:', error)
      alert('❌ Error al restaurar los mensajes por defecto')
    } finally {
      setResetting(false)
    }
  }

  const getTemplateForTipo = (tipo: TipoMensaje): MensajeTemplateList | undefined => {
    return templates.find((t) => t.tipo === tipo)
  }

  // Verificar que el usuario sea ADMIN (después de todos los hooks)
  if (!isAdmin) {
    return (
      <div className="configuracion-whatsapp-page">
        <Card>
          <h1>⚠️ Acceso Denegado</h1>
          <p>Solo los administradores pueden acceder a la configuración de mensajes de WhatsApp.</p>
        </Card>
      </div>
    )
  }

  return (
    <div className="configuracion-whatsapp-page">
      <header className="page-header">
        <div>
          <h1>💬 Configuración de Mensajes WhatsApp</h1>
          <p className="page-description">
            Personaliza los mensajes que se envían automáticamente a tus clientes por WhatsApp
          </p>
        </div>
        <div className="header-actions">
          <Button variant="secondary" onClick={handleResetAllDefaults} disabled={resetting}>
            🔄 Restaurar Todos por Defecto
          </Button>
        </div>
      </header>

      <div className="content-grid">
        {/* Lista de templates */}
        <div className="templates-column">
          <Card className="templates-list-card">
            <h2>📋 Tipos de Mensajes</h2>
            {loading ? (
              <div className="loading-state">
                <p>Cargando...</p>
              </div>
            ) : (
              <ul className="templates-list">
                {ALL_TIPOS.map((tipo) => {
                  const template = getTemplateForTipo(tipo)
                  const isSelected = selectedTipo === tipo

                  return (
                    <li
                      key={tipo}
                      className={`template-item ${isSelected ? 'selected' : ''}`}
                      onClick={() => setSelectedTipo(tipo)}
                    >
                      <div className="template-header">
                        <div className="template-title">
                          <span className="template-icon">{TIPO_ICONS[tipo]}</span>
                          <span className="template-name">{TIPO_LABELS[tipo]}</span>
                        </div>
                        {template && (
                          <Badge variant={template.activo ? 'success' : 'secondary'}>
                            {template.activo ? 'Activo' : 'Inactivo'}
                          </Badge>
                        )}
                      </div>
                      {template && <p className="template-preview">{template.preview}</p>}
                      {!template && <p className="template-preview empty">Sin configurar</p>}
                      <small className="template-updated">
                        {template
                          ? `Actualizado: ${new Date(template.actualizado_en).toLocaleDateString()}`
                          : 'Usa mensaje por defecto'}
                      </small>
                    </li>
                  )
                })}
              </ul>
            )}
          </Card>

          {/* Guía de variables (visible en desktop) */}
          <div className="variables-guide-desktop">
            <VariablesGuide />
          </div>
        </div>

        {/* Editor de template */}
        <div className="editor-column">
          {selectedTipo ? (
            <TemplateEditor
              tipo={selectedTipo}
              onSaved={handleTemplateUpdated}
              onCancel={() => setSelectedTipo(null)}
            />
          ) : (
            <Card className="editor-placeholder">
              <div className="placeholder-content">
                <span className="placeholder-icon">👈</span>
                <h3>Selecciona un tipo de mensaje</h3>
                <p>Haz clic en un tipo de mensaje de la lista para editarlo</p>
              </div>
            </Card>
          )}

          {/* Guía de variables (visible en mobile) */}
          {selectedTipo && (
            <div className="variables-guide-mobile">
              <VariablesGuide />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
