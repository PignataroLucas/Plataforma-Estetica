// Tipos que coinciden con los modelos de Django

// Tipo genérico para respuestas paginadas de Django REST Framework
export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface CentroEstetica {
  id: number
  nombre: string
  razon_social: string
  cuit: string
  telefono: string
  email: string
  direccion: string
  ciudad: string
  provincia: string
  pais: string
  logo?: string
  activo: boolean
  creado_en: string
  actualizado_en: string
}

export interface Sucursal {
  id: number
  centro_estetica: number
  nombre: string
  direccion: string
  telefono: string
  email: string
  ciudad: string
  provincia: string
  codigo_postal: string
  activa: boolean
  es_principal: boolean
  creado_en: string
  actualizado_en: string
}

export enum Rol {
  ADMIN = 'ADMIN',
  MANAGER = 'MANAGER',
  EMPLEADO = 'EMPLEADO',
}

export interface Usuario {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  centro_estetica: number
  sucursal?: number
  telefono: string
  fecha_nacimiento?: string
  direccion: string
  foto?: string
  rol: Rol
  fecha_ingreso?: string
  especialidades: string
  activo: boolean
  creado_en: string
  actualizado_en: string
}

export interface Cliente {
  id: number
  centro_estetica: number
  nombre: string
  apellido: string
  email: string
  telefono: string
  telefono_alternativo: string
  fecha_nacimiento?: string
  direccion: string
  ciudad: string
  provincia: string
  codigo_postal: string
  tipo_documento: 'DNI' | 'PASAPORTE' | 'OTRO'
  numero_documento: string
  alergias: string
  contraindicaciones: string
  notas_medicas: string
  preferencias: string
  foto?: string
  acepta_promociones: boolean
  acepta_whatsapp: boolean
  activo: boolean
  creado_en: string
  actualizado_en: string
  ultima_visita?: string
}

export interface CategoriaServicio {
  id: number
  sucursal: number
  nombre: string
  descripcion: string
  color: string
  activa: boolean
  creado_en: string
  actualizado_en: string
}

export interface Servicio {
  id: number
  sucursal: number
  categoria?: number
  nombre: string
  descripcion: string
  codigo: string
  duracion_minutos: number
  precio: number
  comision_porcentaje: number
  requiere_profesional: boolean
  requiere_equipamiento: string
  activo: boolean
  color: string
  creado_en: string
  actualizado_en: string
}

export enum EstadoTurno {
  PENDIENTE = 'PENDIENTE',
  CONFIRMADO = 'CONFIRMADO',
  COMPLETADO = 'COMPLETADO',
  CANCELADO = 'CANCELADO',
  NO_SHOW = 'NO_SHOW',
}

export enum EstadoPago {
  PENDIENTE = 'PENDIENTE',
  CON_SENA = 'CON_SENA',
  PAGADO = 'PAGADO',
}

export interface Turno {
  id: number
  sucursal: number
  cliente: number
  servicio: number
  profesional?: number
  fecha_hora_inicio: string
  fecha_hora_fin: string
  estado: EstadoTurno
  estado_pago: EstadoPago
  notas: string
  monto_sena?: number
  monto_total: number
  recordatorio_24h_enviado: boolean
  recordatorio_2h_enviado: boolean
  creado_en: string
  actualizado_en: string
  creado_por?: number
}

// Turno con datos nested para listados
export interface TurnoList extends Turno {
  cliente_nombre: string
  servicio_nombre: string
  profesional_nombre?: string
  duracion_minutos: number
}

// Turno con objetos completos nested para detalle
export interface TurnoDetail extends Turno {
  cliente_data: Cliente
  servicio_data: Servicio
  profesional_data?: Usuario
  creado_por_data?: Usuario
}

export interface CategoriaProducto {
  id: number
  sucursal: number
  nombre: string
  descripcion: string
  activa: boolean
  creado_en: string
  actualizado_en: string
}

export interface Proveedor {
  id: number
  sucursal: number
  nombre: string
  razon_social: string
  cuit: string
  telefono: string
  email: string
  direccion: string
  sitio_web: string
  notas: string
  activo: boolean
  creado_en: string
  actualizado_en: string
}

export enum TipoProducto {
  REVENTA = 'REVENTA',
  USO_INTERNO = 'USO_INTERNO',
  INSUMO = 'INSUMO',
}

export interface Producto {
  id: number
  sucursal: number
  categoria?: number
  proveedor?: number
  nombre: string
  descripcion: string
  marca: string
  codigo_barras: string
  sku: string
  tipo: TipoProducto
  stock_actual: number
  stock_minimo: number
  stock_maximo?: number
  unidad_medida: string
  precio_costo: number
  precio_venta: number
  activo: boolean
  foto?: string
  creado_en: string
  actualizado_en: string
}

export enum TipoTransaccion {
  INGRESO_SERVICIO = 'INGRESO_SERVICIO',
  INGRESO_PRODUCTO = 'INGRESO_PRODUCTO',
  INGRESO_OTRO = 'INGRESO_OTRO',
  GASTO_SUELDO = 'GASTO_SUELDO',
  GASTO_ALQUILER = 'GASTO_ALQUILER',
  GASTO_INSUMO = 'GASTO_INSUMO',
  GASTO_SERVICIO = 'GASTO_SERVICIO',
  GASTO_MARKETING = 'GASTO_MARKETING',
  GASTO_OTRO = 'GASTO_OTRO',
}

export enum MetodoPago {
  EFECTIVO = 'EFECTIVO',
  TRANSFERENCIA = 'TRANSFERENCIA',
  TARJETA_DEBITO = 'TARJETA_DEBITO',
  TARJETA_CREDITO = 'TARJETA_CREDITO',
  MERCADOPAGO = 'MERCADOPAGO',
  OTRO = 'OTRO',
}

export interface Transaccion {
  id: number
  sucursal: number
  categoria?: number
  cliente?: number
  turno?: number
  producto?: number
  tipo: TipoTransaccion
  monto: number
  metodo_pago: MetodoPago
  fecha: string
  descripcion: string
  notas: string
  numero_comprobante: string
  archivo_comprobante?: string
  registrado_por?: number
  creado_en: string
  actualizado_en: string
}

export interface Comision {
  id: number
  usuario: number
  turno?: number
  monto_base: number
  porcentaje: number
  monto_comision: number
  pagada: boolean
  fecha_pago?: string
  notas: string
  creado_en: string
  actualizado_en: string
}

export interface HistorialCliente {
  id: number
  cliente: number
  servicio?: number
  profesional?: number
  fecha: string
  observaciones: string
  resultado: string
  foto_antes?: string
  foto_despues?: string
  creado_en: string
  actualizado_en: string
}

export enum TipoNotificacion {
  CONFIRMACION = 'CONFIRMACION',
  RECORDATORIO_24H = 'RECORDATORIO_24H',
  RECORDATORIO_2H = 'RECORDATORIO_2H',
  CANCELACION = 'CANCELACION',
  MODIFICACION = 'MODIFICACION',
  SEGUIMIENTO = 'SEGUIMIENTO',
  PROMOCION = 'PROMOCION',
  OTRO = 'OTRO',
}

export enum EstadoNotificacion {
  PENDIENTE = 'PENDIENTE',
  ENVIADO = 'ENVIADO',
  ENTREGADO = 'ENTREGADO',
  LEIDO = 'LEIDO',
  FALLIDO = 'FALLIDO',
}

export interface Notificacion {
  id: number
  sucursal: number
  cliente: number
  turno?: number
  tipo: TipoNotificacion
  mensaje: string
  telefono_destino: string
  estado: EstadoNotificacion
  mensaje_id_externo: string
  error_mensaje: string
  creado_en: string
  enviado_en?: string
  entregado_en?: string
  leido_en?: string
}

// Tipos para las respuestas de autenticación
export interface LoginResponse {
  access: string
  refresh: string
  user: Usuario
}

export interface TokenRefreshResponse {
  access: string
}

// Tipos para formularios
export interface LoginFormData {
  username: string
  password: string
}

// Tipos para paginación
export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}
