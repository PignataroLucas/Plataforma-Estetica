import { useQuery } from '@tanstack/react-query';

import { getDescuentoApp } from '@/services/descuento';
import { useAuthStore } from '@/stores/auth';
import { aNumero } from '@/utils/precios';

import { useCentroActivo } from './useCentroActivo';

/**
 * El descuento de la app para la clienta logueada.
 *
 * Sin sesión devuelve 0 y el catálogo muestra precio de lista, que es lo
 * correcto: el descuento es de la app y de la clienta, no del producto
 * (COMPRA_EN_APP_SPEC.md §5.8).
 *
 * Un error tampoco inventa un descuento. Mostrar de menos y cobrar de más es
 * justo la trampa del §6.1: si el backend no contesta, la clienta ve el precio
 * de lista, que es el que Tienda Nube va a cobrar de todos modos.
 */
export function useDescuentoApp() {
  const { centroId } = useCentroActivo();
  const autenticada = useAuthStore((s) => s.status === 'authenticated');

  const { data, isPending } = useQuery({
    queryKey: ['descuento-app', centroId],
    queryFn: () => getDescuentoApp(centroId),
    enabled: autenticada,
    // El porcentaje lo cambia el centro desde el CRM y no cada minuto, pero
    // tampoco puede quedar viejo toda la sesión: lo que se muestra tiene que
    // seguir siendo lo que se cobra.
    staleTime: 5 * 60 * 1000,
  });

  return {
    porcentaje: data ? aNumero(data.porcentaje) : 0,
    segmento: data?.segmento ?? null,
    cargando: autenticada && isPending,
  };
}
