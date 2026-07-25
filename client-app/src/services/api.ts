import { API_BASE_URL } from './config';

/**
 * Error de API con un mensaje amigable ya resuelto y, cuando aplica, los
 * errores por campo que devuelve DRF (para pintarlos en los formularios).
 */
export class ApiError extends Error {
  status: number;
  /** { email: 'Ya existe una cuenta…', codigo: 'Código inválido' } */
  fields: Record<string, string>;

  constructor(status: number, message: string, fields: Record<string, string> = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.fields = fields;
  }
}

/** Un valor de error de DRF puede venir como string o como lista de strings. */
function primerMensaje(valor: unknown): string {
  if (Array.isArray(valor)) return String(valor[0] ?? '');
  return String(valor ?? '');
}

/**
 * Traduce el cuerpo de una respuesta de error de DRF a un ApiError.
 * Contempla `{detail}`, `{campo: [msg]}` y `{non_field_errors: [...]}`.
 */
function buildApiError(status: number, body: unknown): ApiError {
  if (body && typeof body === 'object') {
    const obj = body as Record<string, unknown>;

    if (typeof obj.detail === 'string') {
      return new ApiError(status, obj.detail);
    }

    const fields: Record<string, string> = {};
    for (const [key, value] of Object.entries(obj)) {
      fields[key] = primerMensaje(value);
    }

    // Mensaje general: el error de nivel formulario o el primer campo con error.
    const general =
      fields.non_field_errors ||
      fields.detail ||
      Object.values(fields).find(Boolean) ||
      '';
    if (general) return new ApiError(status, general, fields);
  }

  return new ApiError(status, `Error ${status}. Intentá de nuevo.`);
}

/** URL absoluta para un path relativo a la API. */
export const apiUrl = (path: string): string => `${API_BASE_URL}${path}`;

/** Headers JSON base; agrega Content-Type solo si hay cuerpo. */
export function jsonHeaders(init: RequestInit = {}): HeadersInit {
  return {
    Accept: 'application/json',
    ...(init.body ? { 'Content-Type': 'application/json' } : null),
    ...init.headers,
  };
}

/** Lee y tipa una respuesta ya recibida. Lanza `ApiError` si no es 2xx. */
export async function parseResponse<T>(res: Response): Promise<T> {
  if (res.status === 204) return undefined as T;
  const text = await res.text();
  const body = text ? safeJson(text) : null;
  if (!res.ok) throw buildApiError(res.status, body);
  return body as T;
}

/** Núcleo de request tipado contra la API. Lanza `ApiError` si no es 2xx. */
export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let res: Response;
  try {
    res = await fetch(apiUrl(path), { ...init, headers: jsonHeaders(init) });
  } catch {
    // fetch solo rechaza por fallas de red/CORS, no por status HTTP.
    throw new ApiError(0, 'No pudimos conectar. Revisá tu conexión.');
  }
  return parseResponse<T>(res);
}

function safeJson(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

/** GET tipado (sin auth). */
export function apiGet<T>(path: string): Promise<T> {
  return request<T>(path);
}

/** POST tipado con cuerpo JSON (sin auth). */
export function apiPost<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, { method: 'POST', body: JSON.stringify(body) });
}
