import { useEffect } from 'react'
import { createPortal } from 'react-dom'
import {
  ModalProps,
  ModalHeaderProps,
  ModalBodyProps,
  ModalFooterProps,
} from './Modal.types'

/**
 * Modal Component - Composition Pattern
 * Aplica principios SOLID:
 * - SRP: Solo maneja renderizado de modal
 * - OCP: Extensible via composición (ModalHeader, ModalBody, ModalFooter)
 * - DIP: Depende de abstracción (props callbacks)
 */
const Modal = ({
  isOpen,
  onClose,
  children,
  size = 'md',
  closeOnOverlayClick = true,
  closeOnEsc = true,
  showCloseButton = true,
}: ModalProps) => {
  // Manejar cierre con tecla ESC (SRP - responsabilidad única)
  useEffect(() => {
    if (!isOpen || !closeOnEsc) return

    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }

    document.addEventListener('keydown', handleEsc)
    return () => document.removeEventListener('keydown', handleEsc)
  }, [isOpen, closeOnEsc, onClose])

  // Prevenir scroll del body cuando modal está abierto
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }

    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isOpen])

  if (!isOpen) return null

  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
    full: 'max-w-full mx-4',
  }

  const handleOverlayClick = () => {
    if (closeOnOverlayClick) {
      onClose()
    }
  }

  const handleContentClick = (e: React.MouseEvent) => {
    e.stopPropagation()
  }

  const modalContent = (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4"
      onClick={handleOverlayClick}
    >
      <div
        className={`
          relative bg-white rounded-lg shadow-xl w-full
          ${sizeClasses[size]}
          animate-fadeIn
        `}
        onClick={handleContentClick}
      >
        {showCloseButton && (
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="Cerrar modal"
          >
            <svg
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        )}
        {children}
      </div>
    </div>
  )

  return createPortal(modalContent, document.body)
}

/**
 * ModalHeader - Componente composable
 */
export const ModalHeader = ({ children, className = '', ...rest }: ModalHeaderProps) => {
  return (
    <div className={`px-6 py-4 border-b border-gray-200 ${className}`} {...rest}>
      {children}
    </div>
  )
}

/**
 * ModalBody - Componente composable
 */
export const ModalBody = ({ children, className = '', ...rest }: ModalBodyProps) => {
  return (
    <div className={`px-6 py-4 ${className}`} {...rest}>
      {children}
    </div>
  )
}

/**
 * ModalFooter - Componente composable
 */
export const ModalFooter = ({ children, className = '', ...rest }: ModalFooterProps) => {
  return (
    <div className={`px-6 py-4 border-t border-gray-200 flex justify-end gap-2 ${className}`} {...rest}>
      {children}
    </div>
  )
}

export default Modal
