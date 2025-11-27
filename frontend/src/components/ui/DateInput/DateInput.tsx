import { useState, useEffect, useRef } from 'react'
import { formatDateArgentina, parseDateArgentina, formatDateForInput } from '@/utils/dateUtils'

interface DateInputProps {
  label?: string
  value: string // YYYY-MM-DD format
  onChange: (value: string) => void // Returns YYYY-MM-DD format
  error?: string
  helperText?: string
  required?: boolean
  min?: string // YYYY-MM-DD format
  max?: string // YYYY-MM-DD format
  disabled?: boolean
  name?: string
  id?: string
  className?: string
}

/**
 * DateInput - Custom date input component with DD/MM/YYYY format for Argentina
 *
 * Features:
 * - Displays and accepts input in DD/MM/YYYY format
 * - Native date picker as fallback
 * - Automatic formatting and validation
 * - Converts to/from YYYY-MM-DD for API compatibility
 */
export const DateInput = ({
  label,
  value,
  onChange,
  error,
  helperText,
  required = false,
  min,
  max,
  disabled = false,
  name,
  id,
  className = '',
}: DateInputProps) => {
  const inputId = id || `date-input-${Math.random().toString(36).substr(2, 9)}`
  const hiddenInputRef = useRef<HTMLInputElement>(null)

  // Display value in DD/MM/YYYY format
  const [displayValue, setDisplayValue] = useState('')

  // Initialize display value
  useEffect(() => {
    if (value) {
      try {
        // Use formatDateArgentina which handles YYYY-MM-DD correctly
        setDisplayValue(formatDateArgentina(value))
      } catch (e) {
        setDisplayValue('')
      }
    } else {
      setDisplayValue('')
    }
  }, [value])

  /**
   * Handle text input change (DD/MM/YYYY format)
   */
  const handleTextChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let input = e.target.value.replace(/[^0-9/]/g, '') // Only numbers and /

    // Auto-format as user types
    if (input.length === 2 && displayValue.length === 1) {
      input += '/'
    } else if (input.length === 5 && displayValue.length === 4) {
      input += '/'
    }

    // Limit length to DD/MM/YYYY (10 characters)
    if (input.length > 10) {
      input = input.substring(0, 10)
    }

    setDisplayValue(input)

    // If complete date (DD/MM/YYYY), validate and convert
    if (input.length === 10) {
      const parsed = parseDateArgentina(input)
      if (parsed && !isNaN(parsed.getTime())) {
        // Check min/max constraints
        if (min) {
          // Parse min date correctly (YYYY-MM-DD format)
          const [year, month, day] = min.split('-').map(Number)
          const minDate = new Date(year, month - 1, day)
          if (parsed < minDate) return
        }
        if (max) {
          // Parse max date correctly (YYYY-MM-DD format)
          const [year, month, day] = max.split('-').map(Number)
          const maxDate = new Date(year, month - 1, day)
          if (parsed > maxDate) return
        }

        // Convert to YYYY-MM-DD for API
        onChange(formatDateForInput(parsed))
      }
    }
  }

  /**
   * Handle native date picker change
   */
  const handleDatePickerChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const pickedDate = e.target.value // YYYY-MM-DD format
    if (pickedDate) {
      onChange(pickedDate)
    }
  }

  /**
   * Open native date picker
   */
  const openDatePicker = () => {
    hiddenInputRef.current?.showPicker?.()
  }

  const inputClasses = `
    px-3 py-2 border rounded-lg
    focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
    disabled:bg-gray-100 disabled:cursor-not-allowed
    ${error ? 'border-red-500' : 'border-gray-300'}
    ${className}
  `.trim()

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={inputId}
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}

      <div className="relative">
        {/* Text input for DD/MM/YYYY */}
        <input
          type="text"
          id={inputId}
          name={name}
          value={displayValue}
          onChange={handleTextChange}
          placeholder="DD/MM/YYYY"
          required={required}
          disabled={disabled}
          className={`${inputClasses} pr-10`}
          maxLength={10}
        />

        {/* Calendar icon button to open native picker */}
        <button
          type="button"
          onClick={openDatePicker}
          disabled={disabled}
          className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700 disabled:opacity-50"
          title="Abrir calendario"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
        </button>

        {/* Hidden native date picker */}
        <input
          ref={hiddenInputRef}
          type="date"
          value={value}
          onChange={handleDatePickerChange}
          min={min}
          max={max}
          disabled={disabled}
          className="absolute opacity-0 pointer-events-none"
          tabIndex={-1}
        />
      </div>

      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}

      {!error && helperText && (
        <p className="mt-1 text-sm text-gray-500">{helperText}</p>
      )}
    </div>
  )
}

export default DateInput
