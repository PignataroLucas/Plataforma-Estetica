import { ReactNode, HTMLAttributes } from 'react'

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  children: ReactNode
  variant?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'gray'
  size?: 'sm' | 'md' | 'lg'
  dot?: boolean
}
