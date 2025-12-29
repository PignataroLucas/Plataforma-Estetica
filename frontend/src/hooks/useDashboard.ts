import { useState, useEffect } from 'react';
import api from '../services/api';

export interface ProximaCita {
  id: number;
  hora: string;
  cliente: string;
  servicio: string;
  profesional: string;
  estado: string;
}

export interface Alerta {
  tipo: string;
  severidad: 'info' | 'warning' | 'error';
  titulo: string;
  mensaje: string;
  count: number;
}

export interface DashboardHomeData {
  fecha: string;
  can_view_financials: boolean;
  user_role: 'ADMIN' | 'MANAGER' | 'EMPLEADO';
  citas_hoy: {
    total: number;
    pendientes: number;
    confirmadas: number;
    completadas: number;
    canceladas: number;
    no_show: number;
    proximas: ProximaCita[];
  };
  ingresos_hoy: {
    ingresos: number;
    gastos: number;
    neto: number;
  };
  ingresos_mes: {
    ingresos: number;
    gastos: number;
    neto: number;
  };
  clientes_atendidos_hoy: number;
  alertas: Alerta[];
}

export interface DashboardStats {
  total_clientes: number;
  servicios_mes: number;
  productos_criticos: number;
  ocupacion_hoy: number;
}

export function useDashboard() {
  const [dashboardData, setDashboardData] = useState<DashboardHomeData | null>(null);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      setError(null);

      const [homeResponse, statsResponse] = await Promise.all([
        api.get('/analytics/dashboard/home/'),
        api.get('/analytics/dashboard/stats/')
      ]);

      setDashboardData(homeResponse.data);
      setStats(statsResponse.data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Error al cargar el dashboard');
      console.error('Error fetching dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  return {
    dashboardData,
    stats,
    loading,
    error,
    refetch: fetchDashboard
  };
}
