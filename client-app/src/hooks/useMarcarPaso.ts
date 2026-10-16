import { useMutation, useQueryClient } from '@tanstack/react-query';

import { analytics } from '@/services/analytics';
import { marcarPaso } from '@/services/rutina';
import type { MiRutina, RutinaItem } from '@/types/api';
import { aplicarTilde } from '@/utils/rutina';

const CLAVE = ['mi-rutina'];
const MUTACION = ['marcar-paso'];

/**
 * Tildar y destildar pasos de la rutina de hoy.
 *
 * El tilde se ve al instante (se escribe en la caché de `['mi-rutina']`, que
 * comparten Inicio y Mi rutina) y después la respuesta del servidor lo
 * confirma. Si la clienta tilda tres pasos seguidos, solo la última respuesta
 * pisa la caché: una respuesta vieja que llega tarde borraría tildes nuevos.
 */
export function useMarcarPaso() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationKey: MUTACION,
    mutationFn: ({ item, hecho }: { item: RutinaItem; hecho: boolean }) => marcarPaso(item.id, hecho),

    onMutate: async ({ item, hecho }) => {
      await queryClient.cancelQueries({ queryKey: CLAVE });
      queryClient.setQueryData<MiRutina>(CLAVE, (datos) => (datos ? aplicarTilde(datos, item, hecho) : datos));
    },

    onSuccess: ({ hoy }, { item, hecho }) => {
      // Esta mutación todavía cuenta como en curso: 1 es "solo yo".
      if (queryClient.isMutating({ mutationKey: MUTACION }) <= 1) {
        queryClient.setQueryData<MiRutina>(CLAVE, (datos) => (datos ? { ...datos, hoy } : datos));
      }
      if (hecho) {
        analytics.rutinaPasoHecho(item.momento);
        if (hoy.momentos[item.momento].cumplido) analytics.rutinaCumplida(item.momento, hoy.racha);
      }
    },

    // Ante un error no se adivina cómo quedó: se vuelve a pedir el estado real.
    onError: () => queryClient.invalidateQueries({ queryKey: CLAVE }),
  });
}
