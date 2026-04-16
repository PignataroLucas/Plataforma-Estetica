import { useState } from 'react'
import { Cliente } from '@/types/models'
import { Table, Column, Badge, Button } from '@/components/ui'

interface ClientesListProps {
  clientes: Cliente[]
  loading?: boolean
  onEdit: (cliente: Cliente) => void
  onDelete: (cliente: Cliente) => void
  onView: (cliente: Cliente) => void
}

const PAGE_SIZE = 10

export default function ClientesList({
  clientes,
  loading = false,
  onEdit,
  onDelete,
  onView,
}: ClientesListProps) {
  const [currentPage, setCurrentPage] = useState(1)

  const totalPages = Math.max(1, Math.ceil(clientes.length / PAGE_SIZE))
  const startIndex = (currentPage - 1) * PAGE_SIZE
  const paginatedClientes = clientes.slice(startIndex, startIndex + PAGE_SIZE)

  // Reset to page 1 if clientes change and current page is out of bounds
  if (currentPage > totalPages && totalPages > 0) {
    setCurrentPage(1)
  }

  const columns: Column<Cliente>[] = [
    {
      key: 'nombre_completo',
      header: 'Nombre Completo',
      accessor: (row) => `${row.nombre} ${row.apellido}`,
      width: '20%',
    },
    {
      key: 'email',
      header: 'Email',
      width: '20%',
    },
    {
      key: 'telefono',
      header: 'Telefono',
      width: '15%',
    },
    {
      key: 'ciudad',
      header: 'Ciudad',
      width: '15%',
    },
    {
      key: 'activo',
      header: 'Estado',
      width: '10%',
      align: 'center',
      accessor: (row) => (
        <Badge variant={row.activo ? 'success' : 'gray'} dot>
          {row.activo ? 'Activo' : 'Inactivo'}
        </Badge>
      ),
    },
    {
      key: 'acepta_whatsapp',
      header: 'WhatsApp',
      width: '10%',
      align: 'center',
      accessor: (row) => (
        row.acepta_whatsapp ? (
          <span className="text-green-600 text-xl">✓</span>
        ) : (
          <span className="text-gray-400 text-xl">✗</span>
        )
      ),
    },
    {
      key: 'acciones',
      header: 'Acciones',
      width: '10%',
      align: 'right',
      accessor: (row) => (
        <div className="flex gap-2 justify-end">
          <button
            onClick={(e) => {
              e.stopPropagation()
              onView(row)
            }}
            className="text-blue-600 hover:text-blue-800 transition-colors"
            title="Ver detalles"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation()
              onEdit(row)
            }}
            className="text-primary-600 hover:text-primary-800 transition-colors"
            title="Editar"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation()
              onDelete(row)
            }}
            className="text-red-600 hover:text-red-800 transition-colors"
            title="Eliminar"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      ),
    },
  ]

  return (
    <div>
      <Table
        data={paginatedClientes}
        columns={columns}
        loading={loading}
        emptyMessage="No se encontraron clientes. Crea uno para comenzar."
        hoverable
        striped
        onRowClick={onView}
      />

      {/* Pagination */}
      {!loading && clientes.length > PAGE_SIZE && (
        <div className="flex items-center justify-between px-6 py-3 border-t border-gray-200">
          <p className="text-sm text-gray-600">
            Mostrando {startIndex + 1}-{Math.min(startIndex + PAGE_SIZE, clientes.length)} de {clientes.length} clientes
          </p>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 text-sm rounded-md border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Anterior
            </button>
            {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
              <button
                key={page}
                onClick={() => setCurrentPage(page)}
                className={`px-3 py-1 text-sm rounded-md ${
                  page === currentPage
                    ? 'bg-blue-600 text-white'
                    : 'border border-gray-300 hover:bg-gray-50'
                }`}
              >
                {page}
              </button>
            ))}
            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 text-sm rounded-md border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Siguiente
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
