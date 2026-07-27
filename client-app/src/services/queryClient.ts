/**
 * Cliente de TanStack Query de la app (singleton).
 *
 * Vive en su propio módulo —y no dentro del layout— para que el store de sesión
 * pueda limpiar el cache al cambiar de cuenta. Es un grafo de dependencias
 * simple a propósito: este archivo no importa nada del proyecto, así que el
 * store lo puede usar sin generar ciclos.
 */
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 60_000 } },
});

/**
 * Borra TODO lo cacheado. Se llama al iniciar y al cerrar sesión.
 *
 * Sin esto, las queries de la cuenta anterior sobreviven al logout: como las
 * claves son las mismas (`['mis-turnos']`, `['mi-rutina']`…), la cuenta que entra
 * después las lee del cache y ve datos ajenos. Y con `staleTime` de 60s ni
 * siquiera vuelve a pedirlos al backend durante ese minuto.
 */
export function limpiarCacheDeDatos(): void {
  queryClient.clear();
}
