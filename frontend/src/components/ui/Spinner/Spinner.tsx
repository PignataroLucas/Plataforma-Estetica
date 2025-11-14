import { SpinnerProps } from './Spinner.types'

/**
 * Spinner Component - Loading Indicator
 * Aplica principios SOLID:
 * - SRP: Solo renderiza indicador de carga
 * - OCP: Extensible via props (size, variant, fullScreen)
 * - ISP: Props específicos y necesarios
 */
const Spinner = ({
  size = 'md',
  variant = 'primary',
  fullScreen = false,
  className = '',
  ...rest
}: SpinnerProps) => {
  const sizeClasses = {
    sm: 'h-4 w-4 border-2',
    md: 'h-8 w-8 border-2',
    lg: 'h-12 w-12 border-3',
    xl: 'h-16 w-16 border-4',
  }

  const variantClasses = {
    primary: 'border-primary-600 border-t-transparent',
    secondary: 'border-gray-600 border-t-transparent',
    white: 'border-white border-t-transparent',
  }

  const spinnerClasses = `
    animate-spin rounded-full
    ${sizeClasses[size]}
    ${variantClasses[variant]}
    ${className}
  `.trim()

  if (fullScreen) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50">
        <div className={spinnerClasses} {...rest} />
      </div>
    )
  }

  return <div className={spinnerClasses} {...rest} />
}

export default Spinner
