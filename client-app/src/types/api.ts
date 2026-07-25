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

/* ------------------------------------------------------------------ *
 * "Mi rutina" — rutina de cuidado + plan del cliente vinculado
 * ------------------------------------------------------------------ */

export type MomentoRutina = 'DIURNA' | 'NOCTURNA';

/** Un paso de la rutina; `producto` viene del catálogo si el staff lo linkeó. */
export interface RutinaItem {
  id: number;
  momento: MomentoRutina;
  orden: number;
  paso: string;
  producto: ProductoPublico | null;
  producto_texto: string;
  nota: string;
}

export interface RutinaApp {
  id: number;
  activa: boolean;
  actualizado_en: string;
  // Fallback de texto libre para rutinas viejas sin items estructurados
  rutina_diurna_pasos: string;
  rutina_diurna_productos: string;
  rutina_nocturna_pasos: string;
  rutina_nocturna_productos: string;
  items: RutinaItem[];
}

export interface PlanApp {
  id: number;
  tratamiento_sugerido: string;
  frecuencia: string;
  sesiones_estimadas: number | null;
  indicaciones: string;
  proximo_turno: string | null;
  actualizado_en: string;
}

/** Respuesta de GET /api/client/mi-rutina/. */
export interface MiRutina {
  centro: { id: number; nombre: string };
  cliente: { id: number; nombre: string };
  rutina: RutinaApp | null;
  plan: PlanApp | null;
}

/* ------------------------------------------------------------------ *
 * Turnos — listado, disponibilidad y reserva
 * ------------------------------------------------------------------ */

export type EstadoTurno = 'PENDIENTE' | 'CONFIRMADO' | 'COMPLETADO' | 'CANCELADO' | 'NO_SHOW';
export type EstadoPagoTurno = 'PENDIENTE' | 'CON_SENA' | 'PAGADO';

/** Turno como lo devuelve client_api (serializer curado, sin datos internos). */
export interface TurnoApp {
  id: number;
  fecha_hora_inicio: string;
  fecha_hora_fin: string;
  estado: EstadoTurno;
  estado_display: string;
  estado_pago: EstadoPagoTurno;
  estado_pago_display: string;
  servicio: number;
  servicio_nombre: string;
  duracion_minutos: number;
  profesional_nombre: string | null;
  sucursal_nombre: string;
  sucursal_direccion: string;
  centro_nombre: string;
  monto_total: string;
  notas: string;
  /** El backend decide si está a tiempo de cancelarlo (24 hs de antelación). */
  puede_cancelar: boolean;
}

/** Respuesta de GET /api/client/turnos/. */
export interface MisTurnos {
  proximos: TurnoApp[];
  historicos: TurnoApp[];
}

/** Un horario libre; `inicio` es el ISO que se manda tal cual al reservar. */
export interface SlotDisponible {
  inicio: string;
  fin: string;
  hora: string;
  profesional_nombre: string | null;
}

/** Respuesta de GET /api/client/turnos/disponibilidad/. */
export interface Disponibilidad {
  fecha: string;
  servicio?: {
    id: number;
    nombre: string;
    duracion_minutos: number;
    precio: string;
  };
  slots: SlotDisponible[];
}

/** Cuerpo de POST /api/client/turnos/. */
export interface ReservaPayload {
  servicio: number;
  fecha_hora_inicio: string;
  notas?: string;
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
