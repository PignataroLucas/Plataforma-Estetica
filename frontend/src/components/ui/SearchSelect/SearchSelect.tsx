import { useState, useRef, useEffect } from 'react'

export interface SearchSelectOption {
  value: string
  label: string
}

interface SearchSelectProps {
  label?: string
  options: SearchSelectOption[]
  value: string
  onChange: (value: string) => void
  placeholder?: string
  required?: boolean
  error?: string
  disabled?: boolean
}

const SearchSelect = ({
  label,
  options,
  value,
  onChange,
  placeholder = 'Buscar...',
  required = false,
  error,
  disabled = false,
}: SearchSelectProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const [search, setSearch] = useState('')
  const containerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const selectedOption = options.find(o => o.value === value)

  const filtered = search
    ? options.filter(o => o.label.toLowerCase().includes(search.toLowerCase()))
    : options

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false)
        setSearch('')
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSelect = (optionValue: string) => {
    onChange(optionValue)
    setIsOpen(false)
    setSearch('')
  }

  const handleInputFocus = () => {
    if (!disabled) {
      setIsOpen(true)
      setSearch('')
    }
  }

  const handleClear = () => {
    onChange('')
    setSearch('')
    inputRef.current?.focus()
  }

  return (
    <div ref={containerRef} className="relative w-full">
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}

      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          className={`w-full px-3 py-2 pr-8 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors duration-200 disabled:bg-gray-100 disabled:cursor-not-allowed ${
            error ? 'border-red-500' : 'border-gray-300'
          }`}
          value={isOpen ? search : (selectedOption?.label || '')}
          onChange={(e) => setSearch(e.target.value)}
          onFocus={handleInputFocus}
          placeholder={selectedOption ? selectedOption.label : placeholder}
          disabled={disabled}
        />

        {/* Clear / chevron button */}
        {value && !isOpen ? (
          <button
            type="button"
            onClick={handleClear}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            tabIndex={-1}
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        ) : (
          <span className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </span>
        )}
      </div>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {filtered.length === 0 ? (
            <div className="px-3 py-2 text-sm text-gray-500">
              No se encontraron resultados
            </div>
          ) : (
            filtered.map(option => (
              <button
                key={option.value}
                type="button"
                onClick={() => handleSelect(option.value)}
                className={`w-full text-left px-3 py-2 text-sm hover:bg-blue-50 transition-colors ${
                  option.value === value ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-900'
                }`}
              >
                {option.label}
              </button>
            ))
          )}
        </div>
      )}

      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
    </div>
  )
}

export default SearchSelect
