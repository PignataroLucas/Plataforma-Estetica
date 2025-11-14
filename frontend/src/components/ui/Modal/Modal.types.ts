import { ReactNode, HTMLAttributes } from 'react'

export interface ModalProps {
  isOpen: boolean
  onClose: () => void
  children: ReactNode
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full'
  closeOnOverlayClick?: boolean
  closeOnEsc?: boolean
  showCloseButton?: boolean
}

export interface ModalHeaderProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
}

export interface ModalBodyProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
}

export interface ModalFooterProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
}
