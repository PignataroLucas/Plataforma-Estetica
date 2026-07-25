import { DEFAULT_CENTRO_ID } from '@/services/config';
import { useAuthStore } from '@/stores/auth';

/**
 * Centro donde está vinculada la cuenta.
 *
 * Hoy se usa la primera vinculación; cuando la app soporte varias fichas
 * (multi-centro) este hook es el único punto a cambiar.
 */
export function useCentroActivo() {
  const usuario = useAuthStore((s) => s.usuario);
  const vinculacion = usuario?.vinculaciones?.[0] ?? null;

  return {
    centroId: vinculacion?.centro_id ?? DEFAULT_CENTRO_ID,
    centroNombre: vinculacion?.centro_nombre ?? null,
  };
}
