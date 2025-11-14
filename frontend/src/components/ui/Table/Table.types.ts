import { ReactNode } from 'react'

export interface Column<T> {
  key: string
  header: string
  accessor?: (row: T) => ReactNode
  sortable?: boolean
  width?: string
  align?: 'left' | 'center' | 'right'
}

export interface TableProps<T> {
  data: T[]
  columns: Column<T>[]
  loading?: boolean
  emptyMessage?: string
  onRowClick?: (row: T) => void
  striped?: boolean
  hoverable?: boolean
}
