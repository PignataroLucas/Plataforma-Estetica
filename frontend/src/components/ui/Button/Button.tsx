import { ButtonProps } from './Button.types'

/**
 * Button Component - Siguiendo principio Single Responsibility
 * Responsabilidad única: Renderizar un botón con diferentes variantes
 *
 * Open/Closed: Extensible via props sin modificar el código
 */
const Button = ({
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  loading = false,
  leftIcon,
  rightIcon,
  children,
  className = '',
  disabled,
  ...rest
}: ButtonProps) => {
  // Variantes de estilo (OCP - Open/Closed)
  const variantClasses = {
    primary: 'bg-primary-600 text-white hover:bg-primary-700 active:bg-primary-800',
    secondary: 'bg-gray-200 text-gray-800 hover:bg-gray-300 active:bg-gray-400',
    danger: 'bg-red-600 text-white hover:bg-red-700 active:bg-red-800',
    ghost: 'bg-transparent text-gray-700 hover:bg-gray-100',
  }

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  }

  const baseClasses = 'rounded-lg font-medium transition-colors duration-200 inline-flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed'

  const widthClass = fullWidth ? 'w-full' : ''

  const combinedClasses = `
    ${baseClasses}
    ${variantClasses[variant]}
    ${sizeClasses[size]}
    ${widthClass}
    ${className}
  `.trim()

  return (
    <button
      className={combinedClasses}
      disabled={disabled || loading}
      {...rest}
    >
      {loading && (
        <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      )}
      {!loading && leftIcon && <span>{leftIcon}</span>}
      <span>{children}</span>
      {!loading && rightIcon && <span>{rightIcon}</span>}
    </button>
  )
}

export default Button
