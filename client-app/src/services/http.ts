/**
 * Fetch autenticado contra client_api.
 *
 * Inyecta el access token de la sesión y, si el backend responde 401, intenta
 * UNA renovación y reintenta el request. La renovación es "single-flight":
 * varios requests que caduquen a la vez comparten el mismo refresh (evita rotar
 * el refresh token en paralelo, que lo blacklistearía).
 *
 * Para no depender del store (y evitar ciclos de import), el store se registra
 * vía `configureHttpAuth`: le pasa cómo leer el access token y cómo renovar la
 * sesión. Así `http.ts` no importa `stores/auth` ni `services/auth`.
 */
import { ApiError, apiUrl, jsonHeaders, parseResponse } from './api';

type AccessProvider = () => string | null;
/** Renueva la sesión y devuelve el nuevo access, o null si falló (→ logout). */
type RefreshHandler = () => Promise<string | null>;

let getAccessToken: AccessProvider = () => null;
let refreshSession: RefreshHandler = async () => null;

/** El store llama esto una vez para conectar tokens y renovación al fetch. */
export function configureHttpAuth(opts: {
  getAccessToken: AccessProvider;
  refreshSession: RefreshHandler;
}): void {
  getAccessToken = opts.getAccessToken;
  refreshSession = opts.refreshSession;
}

let refreshInFlight: Promise<string | null> | null = null;

/** Renueva el access token (single-flight). */
function renovarAccess(): Promise<string | null> {
  if (refreshInFlight) return refreshInFlight;
  refreshInFlight = (async () => {
    try {
      return await refreshSession();
    } finally {
      refreshInFlight = null;
    }
  })();
  return refreshInFlight;
}

async function fetchConToken(
  path: string,
  init: RequestInit,
  token: string | null,
): Promise<Response> {
  return fetch(apiUrl(path), {
    ...init,
    headers: {
      ...jsonHeaders(init),
      ...(token ? { Authorization: `Bearer ${token}` } : null),
    },
  });
}

/** Request autenticado tipado. Lanza `ApiError` (incl. 401 tras refresh fallido). */
export async function authRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  let res: Response;
  try {
    res = await fetchConToken(path, init, getAccessToken());

    if (res.status === 401) {
      const nuevoAccess = await renovarAccess();
      if (nuevoAccess) {
        res = await fetchConToken(path, init, nuevoAccess);
      }
    }
  } catch {
    throw new ApiError(0, 'No pudimos conectar. Revisá tu conexión.');
  }

  return parseResponse<T>(res);
}

export function authGet<T>(path: string): Promise<T> {
  return authRequest<T>(path);
}

export function authPost<T>(path: string, body?: unknown): Promise<T> {
  return authRequest<T>(path, {
    method: 'POST',
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
}

export function authPatch<T>(path: string, body: unknown): Promise<T> {
  return authRequest<T>(path, { method: 'PATCH', body: JSON.stringify(body) });
}
