import { BadgeProps } from './Badge.types'

/**
 * Badge Component - Status Indicator
 * Aplica principios SOLID:
 * - SRP: Solo muestra indicadores de estado
 * - OCP: Extensible via props (variant, size, dot)
 * - ISP: Props específicos y necesarios
 *
 * Uso común:
 * - Estados de turno (Confirmado, Pendiente, Cancelado)
 * - Estados de pago (Pagado, Con Seña, Pendiente)
 * - Estados de notificación (Enviado, Leído, Fallido)
 */
const Badge = ({
  children,
  variant = 'gray',
  size = 'md',
  dot = false,
  className = '',
  ...rest
}: BadgeProps) => {
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-2.5 py-0.5',
    lg: 'text-base px-3 py-1',
  }

  const variantClasses = {
    primary: 'bg-primary-100 text-primary-800 border-primary-200',
    success: 'bg-green-100 text-green-800 border-green-200',
    warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    danger: 'bg-red-100 text-red-800 border-red-200',
    info: 'bg-blue-100 text-blue-800 border-blue-200',
    gray: 'bg-gray-100 text-gray-800 border-gray-200',
  }

  const dotVariantClasses = {
    primary: 'bg-primary-600',
    success: 'bg-green-600',
    warning: 'bg-yellow-600',
    danger: 'bg-red-600',
    info: 'bg-blue-600',
    gray: 'bg-gray-600',
  }

  const badgeClasses = `
    inline-flex items-center gap-1.5
    font-medium rounded-full border
    ${sizeClasses[size]}
    ${variantClasses[variant]}
    ${className}
  `.trim()

  return (
    <span className={badgeClasses} {...rest}>
      {dot && (
        <span className={`h-2 w-2 rounded-full ${dotVariantClasses[variant]}`} />
      )}
      {children}
    </span>
  )
}

export default Badge
