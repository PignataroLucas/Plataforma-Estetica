import { InputProps } from './Input.types'

/**
 * Input Component - Siguiendo principio Single Responsibility
 * Responsabilidad única: Renderizar un campo de entrada con label y validación
 *
 * Interface Segregation: Solo las props necesarias
 */
const Input = ({
  label,
  error,
  helperText,
  fullWidth = false,
  className = '',
  id,
  ...rest
}: InputProps) => {
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`

  const widthClass = fullWidth ? 'w-full' : ''

  const inputClasses = `
    px-3 py-2 border rounded-lg
    focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
    disabled:bg-gray-100 disabled:cursor-not-allowed
    ${error ? 'border-red-500' : 'border-gray-300'}
    ${widthClass}
    ${className}
  `.trim()

  return (
    <div className={widthClass}>
      {label && (
        <label
          htmlFor={inputId}
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          {label}
        </label>
      )}

      <input
        id={inputId}
        className={inputClasses}
        {...rest}
      />

      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}

      {!error && helperText && (
        <p className="mt-1 text-sm text-gray-500">{helperText}</p>
      )}
    </div>
  )
}

export default Input
