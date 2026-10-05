import { Outlet, Link, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import {
  LayoutDashboard,
  Users,
  Calendar,
  Briefcase,
  Package,
  DollarSign,
  Wallet,
  UserCog,
  BarChart3,
  MessageSquare,
  Inbox,
  LogOut,
  LucideIcon,
} from 'lucide-react'

import { usePedidosPendientes } from '@/hooks/usePedidosPendientes'

interface NavigationItem {
  name: string
  href: string
  icon: LucideIcon
  roles?: string[] // Roles permitidos para ver este item. Si no se especifica, todos pueden verlo
}

const navigation: NavigationItem[] = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard }, // Todos
  { name: 'Clientes', href: '/clientes', icon: Users }, // Todos
  { name: 'Turnos', href: '/turnos', icon: Calendar }, // Todos
  // La cola de pedidos de la app. Va separada de Turnos porque es otra cosa: la
  // agenda se mira, esto se resuelve (APROBACION_TURNOS_SPEC.md §2.7).
  { name: 'Pedidos', href: '/pedidos', icon: Inbox }, // Todos
  { name: 'Servicios', href: '/servicios', icon: Briefcase }, // Todos
  { name: 'Inventario', href: '/inventario', icon: Package, roles: ['ADMIN', 'MANAGER'] },
  { name: 'Finanzas', href: '/finanzas', icon: DollarSign, roles: ['ADMIN'] },
  { name: 'Mi Caja', href: '/mi-caja', icon: Wallet }, // Todos
  { name: 'Empleados', href: '/empleados', icon: UserCog, roles: ['ADMIN', 'MANAGER'] },
  { name: 'Analytics', href: '/analytics', icon: BarChart3, roles: ['ADMIN', 'MANAGER'] },
  { name: 'WhatsApp', href: '/configuracion-whatsapp', icon: MessageSquare, roles: ['ADMIN'] },
]

export default function Layout() {
  const location = useLocation()
  const { user, logout } = useAuthStore()
  // El contador vive en el Layout para que se vea desde cualquier pantalla: un
  // pedido con tres horas de plazo no puede depender de que alguien entre a
  // mirar la sección.
  const { cantidad: pedidosPendientes } = usePedidosPendientes()

  const handleLogout = () => {
    logout()
  }

  // Filtrar navegación según el rol del usuario
  const filteredNavigation = navigation.filter((item) => {
    // Si no tiene roles especificados, todos pueden verlo
    if (!item.roles) return true
    // Si tiene roles, verificar que el usuario tenga uno de esos roles
    return user?.rol && item.roles.includes(user.rol)
  })

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 w-64 bg-white border-r border-gray-200">
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center h-16 px-6 border-b border-gray-200">
            <h1 className="text-xl font-bold text-primary-600">
              Plataforma Estética
            </h1>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
            {filteredNavigation.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.href

              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                    isActive
                      ? 'bg-primary-50 text-primary-600'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <Icon className="w-5 h-5 mr-3" />
                  <span className="flex-1">{item.name}</span>
                  {item.href === '/pedidos' && pedidosPendientes > 0 && (
                    <span className="ml-2 px-2 py-0.5 text-xs font-semibold rounded-full bg-amber-100 text-amber-800">
                      {pedidosPendientes}
                    </span>
                  )}
                </Link>
              )
            })}
          </nav>

          {/* User Info & Logout */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex items-center mb-2">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">
                  {user?.first_name} {user?.last_name}
                </p>
                <p className="text-xs text-gray-500">{user?.email}</p>
                {user?.rol && (
                  <p className="text-xs text-primary-600 font-semibold mt-1">
                    {user.rol === 'ADMIN' && '👑 Administrador'}
                    {user.rol === 'MANAGER' && '⭐ Manager'}
                    {user.rol === 'EMPLEADO' && '👤 Empleado'}
                  </p>
                )}
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center w-full px-3 py-2 text-sm font-medium text-gray-700 rounded-lg hover:bg-gray-100"
            >
              <LogOut className="w-5 h-5 mr-3" />
              Cerrar Sesión
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="pl-64">
        <div className="px-8 py-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
