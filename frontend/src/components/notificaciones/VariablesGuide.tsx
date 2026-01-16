import { useState, useEffect } from 'react'
import { mensajesTemplatesApi } from '@/services/api'
import type { VariablesDisponibles } from '@/types/models'
import Card from '@/components/ui/Card/Card'
import './VariablesGuide.css'

interface Props {
  onInsertVariable?: (variable: string) => void
}

export default function VariablesGuide({ onInsertVariable }: Props) {
  const [variables, setVariables] = useState<VariablesDisponibles | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadVariables()
  }, [])

  const loadVariables = async () => {
    try {
      setLoading(true)
      const response = await mensajesTemplatesApi.variablesDisponibles()
      setVariables(response.data)
    } catch (error) {
      console.error('Error cargando variables:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Card className="variables-guide">
        <h3>Variables Disponibles</h3>
        <p>Cargando...</p>
      </Card>
    )
  }

  if (!variables) {
    return (
      <Card className="variables-guide">
        <h3>Variables Disponibles</h3>
        <p>No se pudieron cargar las variables</p>
      </Card>
    )
  }

  return (
    <Card className="variables-guide">
      <h3>📋 Variables Disponibles</h3>
      <p className="guide-description">
        Usa estas variables en tus mensajes y se reemplazarán automáticamente con los datos reales.
      </p>

      <div className="variables-section">
        <h4>🌐 Variables Generales</h4>
        <div className="variables-list">
          {variables.generales.map((variable) => (
            <div
              key={variable.variable}
              className="variable-item"
              onClick={() => onInsertVariable?.(variable.variable)}
              title="Click para insertar"
            >
              <code>{variable.variable}</code>
              <span className="variable-description">{variable.descripcion}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="variables-section">
        <h4>📅 Variables de Turnos</h4>
        <div className="variables-list">
          {variables.turnos.map((variable) => (
            <div
              key={variable.variable}
              className="variable-item"
              onClick={() => onInsertVariable?.(variable.variable)}
              title="Click para insertar"
            >
              <code>{variable.variable}</code>
              <span className="variable-description">{variable.descripcion}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="usage-example">
        <h4>💡 Ejemplo de uso</h4>
        <div className="example-box">
          <p>
            Hola <code>{'{nombre_cliente}'}</code>! 👋
          </p>
          <p>
            Tu turno es el <code>{'{fecha}'}</code> a las <code>{'{hora}'}</code>
          </p>
          <p className="example-result">
            → Se convertirá en: <br />
            <em>Hola María! 👋 Tu turno es el 25/12/2024 a las 14:30</em>
          </p>
        </div>
      </div>
    </Card>
  )
}
