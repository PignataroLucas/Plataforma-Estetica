import { TableProps, Column } from './Table.types'
import Spinner from '../Spinner/Spinner'

/**
 * Table Component - Generic Data Table
 * Aplica principios SOLID:
 * - SRP: Solo renderiza tablas de datos
 * - OCP: Extensible via columns con custom accessors
 * - LSP: Generic type permite cualquier estructura de datos
 * - ISP: Cada columna define solo lo necesario
 * - DIP: Depende de abstracciones (Column interface, accessor functions)
 *
 * Uso:
 * <Table
 *   data={clientes}
 *   columns={[
 *     { key: 'nombre', header: 'Nombre' },
 *     { key: 'email', header: 'Email' },
 *     { key: 'acciones', header: 'Acciones', accessor: (row) => <Button>Editar</Button> }
 *   ]}
 * />
 */
function Table<T extends Record<string, any>>({
  data,
  columns,
  loading = false,
  emptyMessage = 'No hay datos para mostrar',
  onRowClick,
  striped = true,
  hoverable = true,
}: TableProps<T>) {
  const getAlignClass = (align?: 'left' | 'center' | 'right') => {
    switch (align) {
      case 'center':
        return 'text-center'
      case 'right':
        return 'text-right'
      default:
        return 'text-left'
    }
  }

  const getCellValue = (row: T, column: Column<T>) => {
    if (column.accessor) {
      return column.accessor(row)
    }
    return row[column.key]
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <Spinner size="lg" />
      </div>
    )
  }

  if (data.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        {emptyMessage}
      </div>
    )
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                className={`
                  px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider
                  ${getAlignClass(column.align)}
                `}
                style={{ width: column.width }}
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.map((row, rowIndex) => (
            <tr
              key={rowIndex}
              onClick={() => onRowClick?.(row)}
              className={`
                ${striped && rowIndex % 2 === 1 ? 'bg-gray-50' : 'bg-white'}
                ${hoverable ? 'hover:bg-gray-100 transition-colors' : ''}
                ${onRowClick ? 'cursor-pointer' : ''}
              `}
            >
              {columns.map((column) => (
                <td
                  key={`${rowIndex}-${column.key}`}
                  className={`
                    px-6 py-4 whitespace-nowrap text-sm text-gray-900
                    ${getAlignClass(column.align)}
                  `}
                >
                  {getCellValue(row, column)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default Table
