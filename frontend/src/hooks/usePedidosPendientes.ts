import { useQuery } from '@tanstack/react-query'

import { getPedidosPendientes } from '../services/pedidosService'

/** Clave única, para que invalidar desde cualquier lado refresque el contador. */
export const PEDIDOS_KEY = ['pedidos-pendientes'] as const

/**
 * Cada cuánto se vuelve a preguntar.
 *
 * Es polling y es la decisión correcta, no la fácil: WebSockets significaría un
 * proceso más en Railway y Redis como transporte, para ganar segundos de
 * latencia en algo que pasa un puñado de veces por día
 * (APROBACION_TURNOS_SPEC.md §2.9). Con un plazo de 3 horas para responder,
 * medio minuto de demora en ver el contador no cambia nada.
 */
const CADA = 30 * 1000

export function usePedidosPendientes() {
  const { data, isLoading, refetch } = useQuery({
    queryKey: PEDIDOS_KEY,
    queryFn: getPedidosPendientes,
    refetchInterval: CADA,
    // El default global del CRM lo tiene apagado, pero acá es justo lo que cubre
    // el uso real: vuelve a la pestaña y el contador ya está al día.
    refetchOnWindowFocus: true,
    // Sin cache: un pedido que ya se resolvió no puede seguir contando.
    staleTime: 0,
  })

  return {
    pedidos: data ?? [],
    cantidad: data?.length ?? 0,
    cargando: isLoading,
    refrescar: refetch,
  }
}
