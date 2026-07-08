import { useEffect, useState } from 'react';
import api from '../../services/api';
import { Alerta } from '../../hooks/useDashboard';
import { Modal, ModalHeader, ModalBody, Spinner } from '../ui';

interface StockBajoItem {
  id: number;
  nombre: string;
  sku: string;
  categoria: string | null;
  stock_actual: number;
  stock_minimo: number;
  unidad_medida: string;
}

interface ClienteRiesgoItem {
  id: number;
  nombre_completo: string;
  telefono: string;
  ultima_visita: string | null;
  dias_sin_visita: number | null;
}

interface PagoPendienteItem {
  id: number;
  fecha: string;
  cliente: string;
  telefono: string;
  servicio: string;
  profesional: string;
  monto_total: number;
}

interface CitaPendienteItem {
  id: number;
  hora: string;
  cliente: string;
  telefono: string;
  servicio: string;
  profesional: string;
}

interface AlertaDetalle {
  tipo: string;
  count: number;
  items: StockBajoItem[] | ClienteRiesgoItem[] | PagoPendienteItem[] | CitaPendienteItem[];
}

interface AlertaDetalleModalProps {
  alerta: Alerta;
  onClose: () => void;
}

const formatMonto = (monto: number) =>
  `$${monto.toLocaleString('es-AR', { minimumFractionDigits: 2 })}`;

export default function AlertaDetalleModal({ alerta, onClose }: AlertaDetalleModalProps) {
  const [detalle, setDetalle] = useState<AlertaDetalle | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelado = false;

    const fetchDetalle = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await api.get(`/analytics/dashboard/alertas/${alerta.tipo}/`);
        if (!cancelado) {
          setDetalle(response.data);
        }
      } catch (err: any) {
        if (!cancelado) {
          setError(err.response?.data?.detail || 'Error al cargar el detalle de la alerta');
        }
      } finally {
        if (!cancelado) {
          setLoading(false);
        }
      }
    };

    fetchDetalle();
    return () => {
      cancelado = true;
    };
  }, [alerta.tipo]);

  const renderStockBajo = (items: StockBajoItem[]) => (
    <div className="space-y-3">
      {items.map((producto) => (
        <div
          key={producto.id}
          className="border border-gray-200 rounded-lg p-4 flex items-center justify-between gap-4"
        >
          <div className="min-w-0">
            <p className="font-semibold text-gray-900 truncate">{producto.nombre}</p>
            <p className="text-sm text-gray-500">
              {producto.categoria || 'Sin categoría'}
              {producto.sku && ` · SKU: ${producto.sku}`}
            </p>
          </div>
          <div className="text-right flex-shrink-0">
            <p className={`font-bold ${producto.stock_actual <= 0 ? 'text-red-600' : 'text-yellow-600'}`}>
              {producto.stock_actual} {producto.unidad_medida}
            </p>
            <p className="text-xs text-gray-500">Mínimo: {producto.stock_minimo}</p>
          </div>
        </div>
      ))}
    </div>
  );

  const renderClientesRiesgo = (items: ClienteRiesgoItem[], total: number) => (
    <div className="space-y-3">
      {items.map((cliente) => (
        <div
          key={cliente.id}
          className="border border-gray-200 rounded-lg p-4 flex items-center justify-between gap-4"
        >
          <div className="min-w-0">
            <p className="font-semibold text-gray-900 truncate">{cliente.nombre_completo}</p>
            <p className="text-sm text-gray-500">{cliente.telefono || 'Sin teléfono'}</p>
          </div>
          <div className="text-right flex-shrink-0">
            {cliente.ultima_visita ? (
              <>
                <p className="text-sm font-medium text-gray-900">
                  Última visita: {cliente.ultima_visita}
                </p>
                <p className="text-xs text-yellow-600 font-semibold">
                  Hace {cliente.dias_sin_visita} días
                </p>
              </>
            ) : (
              <p className="text-sm text-gray-500">Sin visitas registradas</p>
            )}
          </div>
        </div>
      ))}
      {total > items.length && (
        <p className="text-sm text-gray-500 text-center pt-2">
          Mostrando los primeros {items.length} de {total} clientes
        </p>
      )}
    </div>
  );

  const renderPagosPendientes = (items: PagoPendienteItem[]) => (
    <div className="space-y-3">
      {items.map((turno) => (
        <div
          key={turno.id}
          className="border border-gray-200 rounded-lg p-4 flex items-center justify-between gap-4"
        >
          <div className="min-w-0">
            <p className="font-semibold text-gray-900 truncate">{turno.cliente}</p>
            <p className="text-sm text-gray-500 truncate">
              {turno.servicio} · {turno.profesional}
            </p>
            <p className="text-xs text-gray-400">{turno.fecha}</p>
          </div>
          <div className="text-right flex-shrink-0">
            <p className="font-bold text-red-600">{formatMonto(turno.monto_total)}</p>
            <p className="text-xs text-gray-500">Pendiente de pago</p>
          </div>
        </div>
      ))}
    </div>
  );

  const renderCitasPendientes = (items: CitaPendienteItem[]) => (
    <div className="space-y-3">
      {items.map((cita) => (
        <div
          key={cita.id}
          className="border border-gray-200 rounded-lg p-4 flex items-center justify-between gap-4"
        >
          <div className="min-w-0">
            <p className="font-semibold text-gray-900 truncate">{cita.cliente}</p>
            <p className="text-sm text-gray-500 truncate">
              {cita.servicio} · {cita.profesional}
            </p>
          </div>
          <div className="text-right flex-shrink-0">
            <p className="font-bold text-blue-600">{cita.hora} hs</p>
            <p className="text-xs text-gray-500">Sin confirmar</p>
          </div>
        </div>
      ))}
    </div>
  );

  const renderContenido = () => {
    if (loading) {
      return (
        <div className="flex justify-center py-12">
          <Spinner size="lg" />
        </div>
      );
    }

    if (error) {
      return (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
          <p className="text-red-600">{error}</p>
        </div>
      );
    }

    if (!detalle || detalle.items.length === 0) {
      return (
        <p className="text-gray-500 text-center py-8">No hay datos para mostrar</p>
      );
    }

    switch (detalle.tipo) {
      case 'stock_bajo':
        return renderStockBajo(detalle.items as StockBajoItem[]);
      case 'clientes_riesgo':
        return renderClientesRiesgo(detalle.items as ClienteRiesgoItem[], detalle.count);
      case 'pagos_pendientes':
        return renderPagosPendientes(detalle.items as PagoPendienteItem[]);
      case 'citas_pendientes':
        return renderCitasPendientes(detalle.items as CitaPendienteItem[]);
      default:
        return (
          <p className="text-gray-500 text-center py-8">
            No hay vista de detalle para esta alerta
          </p>
        );
    }
  };

  return (
    <Modal isOpen onClose={onClose} size="lg">
      <ModalHeader>
        <h3 className="text-lg font-semibold text-gray-900 pr-8">
          {alerta.titulo}
          {detalle && detalle.count > 0 && (
            <span className="ml-2 text-sm font-normal text-gray-500">
              ({detalle.count})
            </span>
          )}
        </h3>
        <p className="text-sm text-gray-500 mt-1">{alerta.mensaje}</p>
      </ModalHeader>
      <ModalBody>{renderContenido()}</ModalBody>
    </Modal>
  );
}
