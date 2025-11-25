import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import LoginPage from '@/pages/LoginPage'
import DashboardPage from '@/pages/DashboardPage'
import ClientesPage from '@/pages/ClientesPage'
import ClienteDetailPage from '@/pages/ClienteDetailPage'
import TurnosPage from '@/pages/TurnosPage'
import ServiciosPage from '@/pages/ServiciosPage'
import InventarioPage from '@/pages/InventarioPage'
import FinanzasPage from '@/pages/FinanzasPage'
import EmpleadosPage from '@/pages/EmpleadosPage'
import AnalyticsPage from '@/pages/AnalyticsPage'
import Layout from '@/components/Layout'

function App() {
  const { isAuthenticated } = useAuthStore()

  return (
    <Routes>
      <Route path="/login" element={!isAuthenticated ? <LoginPage /> : <Navigate to="/" />} />

      <Route element={isAuthenticated ? <Layout /> : <Navigate to="/login" />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/clientes" element={<ClientesPage />} />
        <Route path="/clientes/:id" element={<ClienteDetailPage />} />
        <Route path="/turnos" element={<TurnosPage />} />
        <Route path="/servicios" element={<ServiciosPage />} />
        <Route path="/inventario" element={<InventarioPage />} />
        <Route path="/finanzas" element={<FinanzasPage />} />
        <Route path="/empleados" element={<EmpleadosPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
      </Route>
    </Routes>
  )
}

export default App
