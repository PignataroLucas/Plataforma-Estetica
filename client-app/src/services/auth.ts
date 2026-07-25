/** Llamadas a client_api: autenticación (sin token) y perfil (con token). */
import type { AuthResponse, Perfil, RegistroPayload, TokenPair } from '@/types/api';

import { apiPost } from './api';
import { authGet, authPatch } from './http';

/** POST /api/client/auth/login/ */
export function login(email: string, password: string): Promise<AuthResponse> {
  return apiPost<AuthResponse>('/client/auth/login/', { email, password });
}

/** POST /api/client/auth/registro/ (con código de invitación o auto-registro). */
export function registro(payload: RegistroPayload): Promise<AuthResponse> {
  return apiPost<AuthResponse>('/client/auth/registro/', payload);
}

/**
 * POST /api/client/auth/refresh/ — el backend rota el refresh, así que la
 * respuesta trae un par nuevo (access + refresh).
 */
export function refreshTokens(refresh: string): Promise<TokenPair> {
  return apiPost<TokenPair>('/client/auth/refresh/', { refresh });
}

/** GET /api/client/perfil/ (autenticado). */
export function getPerfil(): Promise<Perfil> {
  return authGet<Perfil>('/client/perfil/');
}

/** PATCH /api/client/perfil/ (autenticado). */
export function actualizarPerfil(datos: { nombre?: string; apellido?: string }): Promise<Perfil> {
  return authPatch<Perfil>('/client/perfil/', datos);
}
