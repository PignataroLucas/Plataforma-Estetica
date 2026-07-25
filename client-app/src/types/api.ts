/** Tipos de las respuestas de la API pública (coinciden con los serializers del backend). */

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface SucursalPublica {
  id: number;
  nombre: string;
  direccion: string;
  ciudad: string;
  provincia: string;
  telefono: string;
}

export interface CentroPublico {
  id: number;
  nombre: string;
  direccion: string;
  ciudad: string;
  provincia: string;
  pais: string;
  telefono: string;
  email: string;
  logo: string | null;
  sucursales: SucursalPublica[];
}

export interface ServicioPublico {
  id: number;
  nombre: string;
  descripcion: string;
  duracion_minutos: number;
  precio: string; // DRF serializa DecimalField como string
  categoria_nombre: string | null;
  color: string;
  sucursal: number;
  sucursal_nombre: string;
}

export interface ProductoPublico {
  id: number;
  nombre: string;
  descripcion: string;
  marca: string;
  precio: string;
  en_oferta: boolean;
  precio_oferta: string | null;
  porcentaje_descuento: number;
  disponible: boolean;
  foto: string | null;
  categoria_nombre: string | null;
  contenido_ml: string | null;
  duracion_estimada_dias: number | null;
  pao_meses: number | null;
  frecuencia_uso: string;
}

/* ------------------------------------------------------------------ *
 * client_api — cuenta de la app (UsuarioCliente) y autenticación
 * ------------------------------------------------------------------ */

/** Vínculo entre la cuenta de app y una ficha de cliente de un centro. */
export interface VinculacionResumen {
  id: number;
  cliente_id: number;
  cliente_nombre: string;
  centro_id: number;
  centro_nombre: string;
  metodo_vinculacion: string;
  vinculado_en: string;
}

/** Perfil devuelto por GET /api/client/perfil/ (y anidado en el login/registro). */
export interface Perfil {
  id: number;
  email: string;
  nombre: string;
  apellido: string;
  email_verificado: boolean;
  push_token: string | null;
  creado_en: string;
  vinculaciones: VinculacionResumen[];
}

/** Par de tokens JWT de cliente (claim token_use='cliente'). */
export interface TokenPair {
  access: string;
  refresh: string;
}

/** Respuesta de login y registro: tokens + perfil de la cuenta. */
export interface AuthResponse extends TokenPair {
  usuario: Perfil;
}

/** Cuerpo de POST /api/client/auth/registro/. */
export interface RegistroPayload {
  email: string;
  password: string;
  /** Flujo con código de invitación (vincula a una ficha existente). */
  codigo?: string;
  /** Auto-registro (sin código): nombre/apellido/centro requeridos. */
  nombre?: string;
  apellido?: string;
  telefono?: string;
  centro?: number;
}
