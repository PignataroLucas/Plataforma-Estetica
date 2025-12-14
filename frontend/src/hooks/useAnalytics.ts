import { useState, useEffect } from 'react';
import api from '../services/api';

interface AnalyticsFilters {
  startDate?: string;
  endDate?: string;
  sucursalId?: number;
  granularity?: 'day' | 'week' | 'month';
  compare?: boolean;
}

export function useAnalytics(filters: AnalyticsFilters = {}) {
  const [summary, setSummary] = useState<any>(null);
  const [revenue, setRevenue] = useState<any>(null);
  const [services, setServices] = useState<any>(null);
  const [products, setProducts] = useState<any>(null);
  const [employees, setEmployees] = useState<any>(null);
  const [clients, setClients] = useState<any>(null);
  const [ocupacion, setOcupacion] = useState<any>(null);
  const [noShows, setNoShows] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAnalytics();
  }, [filters.startDate, filters.endDate, filters.sucursalId, filters.granularity, filters.compare]);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();

      if (filters.startDate) params.append('start_date', filters.startDate);
      if (filters.endDate) params.append('end_date', filters.endDate);
      if (filters.sucursalId) params.append('sucursal_id', filters.sucursalId.toString());
      if (filters.granularity) params.append('granularity', filters.granularity);
      if (filters.compare) params.append('compare', 'true');

      const queryString = params.toString();

      // Fetch all analytics in parallel
      const [
        summaryRes,
        revenueRes,
        servicesRes,
        productsRes,
        employeesRes,
        clientsRes,
        ocupacionRes,
        noShowsRes,
      ] = await Promise.all([
        api.get(`/analytics/dashboard/summary/?${queryString}`),
        api.get(`/analytics/dashboard/revenue/?${queryString}`),
        api.get(`/analytics/dashboard/services/?${queryString}`),
        api.get(`/analytics/dashboard/products/?${queryString}`),
        api.get(`/analytics/dashboard/employees/?${queryString}`),
        api.get(`/analytics/dashboard/clients/?${queryString}`),
        api.get(`/analytics/dashboard/ocupacion/?${queryString}`),
        api.get(`/analytics/dashboard/no-shows/?${queryString}`),
      ]);

      setSummary(summaryRes.data);
      setRevenue(revenueRes.data);
      setServices(servicesRes.data);
      setProducts(productsRes.data);
      setEmployees(employeesRes.data);
      setClients(clientsRes.data);
      setOcupacion(ocupacionRes.data);
      setNoShows(noShowsRes.data);
    } catch (err: any) {
      console.error('Error fetching analytics:', err);
      setError(err.message || 'Error al cargar analytics');
    } finally {
      setLoading(false);
    }
  };

  return {
    summary,
    revenue,
    services,
    products,
    employees,
    clients,
    ocupacion,
    noShows,
    loading,
    error,
    refetch: fetchAnalytics,
  };
}

export function useClientAnalytics(clienteId: number) {
  const [summary, setSummary] = useState<any>(null);
  const [spending, setSpending] = useState<any>(null);
  const [patterns, setPatterns] = useState<any>(null);
  const [alerts, setAlerts] = useState<any>(null);
  const [products, setProducts] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (clienteId) {
      fetchClientAnalytics();
    }
  }, [clienteId]);

  const fetchClientAnalytics = async () => {
    setLoading(true);
    setError(null);

    try {
      const [summaryRes, spendingRes, patternsRes, alertsRes, productsRes] = await Promise.all([
        api.get(`/analytics/client/${clienteId}/summary/`),
        api.get(`/analytics/client/${clienteId}/spending/`),
        api.get(`/analytics/client/${clienteId}/patterns/`),
        api.get(`/analytics/client/${clienteId}/alerts/`),
        api.get(`/analytics/client/${clienteId}/products/`),
      ]);

      setSummary(summaryRes.data);
      setSpending(spendingRes.data);
      setPatterns(patternsRes.data);
      setAlerts(alertsRes.data);
      setProducts(productsRes.data);
    } catch (err: any) {
      console.error('Error fetching client analytics:', err);
      setError(err.message || 'Error al cargar analytics del cliente');
    } finally {
      setLoading(false);
    }
  };

  return {
    summary,
    spending,
    patterns,
    alerts,
    products,
    loading,
    error,
    refetch: fetchClientAnalytics,
  };
}
