import { ReactNode, HTMLAttributes } from 'react'

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
  padding?: 'none' | 'sm' | 'md' | 'lg'
  hover?: boolean
}

export interface CardHeaderProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
}

export interface CardBodyProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
}

export interface CardFooterProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
}
