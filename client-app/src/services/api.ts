import { API_BASE_URL } from './config';

/** GET tipado contra la API. Lanza si la respuesta no es 2xx. */
export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { Accept: 'application/json' },
  });
  if (!res.ok) {
    throw new Error(`Error ${res.status} al pedir ${path}`);
  }
  return (await res.json()) as T;
}
