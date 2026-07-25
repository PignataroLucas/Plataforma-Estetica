/**
 * Store de sesión de la app (Zustand).
 *
 * Única fuente de verdad de los tokens JWT de cliente en memoria y del perfil
 * de la cuenta. Persiste SOLO los tokens (SecureStore / localStorage); el perfil
 * se re-consulta al hidratar. `useAuthStore.getState()` se usa también desde la
 * capa de red (`services/http.ts`) para inyectar y renovar el token.
 */
import { create } from 'zustand';

import {
  getPerfil,
  login as loginReq,
  refreshTokens,
  registro as registroReq,
} from '@/services/auth';
import { configureHttpAuth } from '@/services/http';
import { deleteItem, getItem, setItem } from '@/services/storage';
import type { AuthResponse, Perfil, RegistroPayload, TokenPair } from '@/types/api';

const ACCESS_KEY = 'ame.access';
const REFRESH_KEY = 'ame.refresh';

type Status = 'loading' | 'authenticated' | 'unauthenticated';

interface AuthState {
  status: Status;
  access: string | null;
  refresh: string | null;
  usuario: Perfil | null;

  /** Carga los tokens persistidos y valida la sesión trayendo el perfil. */
  hydrate: () => Promise<void>;
  /** Login por email/contraseña. Propaga `ApiError` para mostrar en el form. */
  iniciarSesion: (email: string, password: string) => Promise<void>;
  /** Registro (con código o auto-registro). Propaga `ApiError`. */
  registrar: (payload: RegistroPayload) => Promise<void>;
  /** Guarda tokens + perfil de una respuesta de login/registro. */
  setSession: (auth: AuthResponse) => Promise<void>;
  /** Reemplaza el par de tokens (tras una rotación en el refresh). */
  setTokens: (par: TokenPair) => Promise<void>;
  /** Actualiza el perfil en memoria (tras un PATCH). */
  setUsuario: (usuario: Perfil) => void;
  /** Cierra sesión y limpia el almacenamiento. */
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  status: 'loading',
  access: null,
  refresh: null,
  usuario: null,

  hydrate: async () => {
    const [access, refresh] = await Promise.all([getItem(ACCESS_KEY), getItem(REFRESH_KEY)]);

    if (!access || !refresh) {
      set({ status: 'unauthenticated', access: null, refresh: null, usuario: null });
      return;
    }

    set({ access, refresh });
    try {
      const usuario = await getPerfil();
      set({ status: 'authenticated', usuario });
    } catch {
      // getPerfil ya intentó renovar el token; si llegó acá la sesión no sirve.
      await get().logout();
    }
  },

  iniciarSesion: async (email, password) => {
    const auth = await loginReq(email, password);
    await get().setSession(auth);
  },

  registrar: async (payload) => {
    const auth = await registroReq(payload);
    await get().setSession(auth);
  },

  setSession: async (auth) => {
    await Promise.all([setItem(ACCESS_KEY, auth.access), setItem(REFRESH_KEY, auth.refresh)]);
    set({
      status: 'authenticated',
      access: auth.access,
      refresh: auth.refresh,
      usuario: auth.usuario,
    });
  },

  setTokens: async (par) => {
    await Promise.all([setItem(ACCESS_KEY, par.access), setItem(REFRESH_KEY, par.refresh)]);
    set({ access: par.access, refresh: par.refresh });
  },

  setUsuario: (usuario) => set({ usuario }),

  logout: async () => {
    await Promise.all([deleteItem(ACCESS_KEY), deleteItem(REFRESH_KEY)]);
    set({ status: 'unauthenticated', access: null, refresh: null, usuario: null });
  },
}));

/**
 * Renovación de sesión para la capa de red. Usa el refresh guardado, persiste
 * el par rotado y, si falla, cierra sesión. El single-flight vive en `http.ts`.
 */
async function refreshSession(): Promise<string | null> {
  const { refresh, setTokens, logout } = useAuthStore.getState();
  if (!refresh) return null;
  try {
    const par = await refreshTokens(refresh);
    await setTokens(par);
    return par.access;
  } catch {
    await logout();
    return null;
  }
}

// Conecta el store a la capa de red sin que `http.ts` importe el store.
configureHttpAuth({
  getAccessToken: () => useAuthStore.getState().access,
  refreshSession,
});
