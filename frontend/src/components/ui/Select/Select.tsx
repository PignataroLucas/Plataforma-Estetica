import { SelectProps } from './Select.types'

/**
 * Select Component - Dropdown Selection
 * Aplica principios SOLID:
 * - SRP: Solo maneja selección de opciones
 * - OCP: Extensible via props
 * - ISP: Props específicos necesarios (label, error, helperText, options)
 */
const Select = ({
  label,
  error,
  helperText,
  options,
  placeholder = 'Seleccionar...',
  fullWidth = false,
  className = '',
  ...rest
}: SelectProps) => {
  const baseClasses = `
    px-3 py-2 border rounded-lg
    focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
    transition-colors duration-200
    disabled:bg-gray-100 disabled:cursor-not-allowed
    ${error ? 'border-red-500' : 'border-gray-300'}
    ${fullWidth ? 'w-full' : ''}
    ${className}
  `.trim()

  return (
    <div className={fullWidth ? 'w-full' : ''}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {rest.required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}

      <select className={baseClasses} {...rest}>
        {placeholder && (
          <option value="" disabled>
            {placeholder}
          </option>
        )}
        {options.map((option) => (
          <option
            key={option.value}
            value={option.value}
            disabled={option.disabled}
          >
            {option.label}
          </option>
        ))}
      </select>

      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}

      {!error && helperText && (
        <p className="mt-1 text-sm text-gray-500">{helperText}</p>
      )}
    </div>
  )
}

export default Select
