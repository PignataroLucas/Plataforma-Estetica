import { CardProps, CardHeaderProps, CardBodyProps, CardFooterProps } from './Card.types'

/**
 * Card Component - Composition Pattern
 * Permite componer cards flexibles sin herencia
 */
const Card = ({
  children,
  padding = 'md',
  hover = false,
  className = '',
  ...rest
}: CardProps) => {
  const paddingClasses = {
    none: '',
    sm: 'p-3',
    md: 'p-6',
    lg: 'p-8',
  }

  const hoverClass = hover ? 'hover:shadow-md transition-shadow duration-200' : ''

  const cardClasses = `
    bg-white rounded-lg shadow-sm border border-gray-200
    ${paddingClasses[padding]}
    ${hoverClass}
    ${className}
  `.trim()

  return (
    <div className={cardClasses} {...rest}>
      {children}
    </div>
  )
}

/**
 * CardHeader - Componente composable (Composition over Inheritance)
 */
export const CardHeader = ({ children, className = '', ...rest }: CardHeaderProps) => {
  return (
    <div className={`border-b border-gray-200 pb-4 mb-4 ${className}`} {...rest}>
      {children}
    </div>
  )
}

/**
 * CardBody - Componente composable
 */
export const CardBody = ({ children, className = '', ...rest }: CardBodyProps) => {
  return (
    <div className={className} {...rest}>
      {children}
    </div>
  )
}

/**
 * CardFooter - Componente composable
 */
export const CardFooter = ({ children, className = '', ...rest }: CardFooterProps) => {
  return (
    <div className={`border-t border-gray-200 pt-4 mt-4 ${className}`} {...rest}>
      {children}
    </div>
  )
}

export default Card
