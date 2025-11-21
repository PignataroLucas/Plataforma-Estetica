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
  sueldo_mensual?: number
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

export interface MaquinaAlquilada {
  id: number
  sucursal: number
  nombre: string
  descripcion: string
  costo_diario: number
  proveedor: string
  activa: boolean
  creado_en: string
  actualizado_en: string
}

export enum EstadoAlquiler {
  PROGRAMADO = 'PROGRAMADO',
  CONFIRMADO = 'CONFIRMADO',
  CANCELADO = 'CANCELADO',
  COBRADO = 'COBRADO',
}

export interface AlquilerMaquina {
  id: number
  sucursal: number
  maquina: number
  maquina_nombre: string
  fecha: string
  estado: EstadoAlquiler
  estado_display: string
  costo: number
  notas: string
  transaccion_gasto: number | null
  tiene_turnos: boolean
  creado_por: number | null
  creado_en: string
  actualizado_en: string
}

export interface AlquilerPendiente {
  maquina_id: number
  maquina_nombre: string
  fecha: string
  cantidad_turnos: number
  costo_diario: number
  alquiler_id: number | null
  estado: EstadoAlquiler | null
}

export interface Servicio {
  id: number
  sucursal: number
  categoria?: number
  maquina_alquilada?: number
  maquina_nombre?: string
  nombre: string
  descripcion: string
  codigo: string
  duracion_minutos: number
  precio: number
  costo_maquina_diario: number
  ganancia_por_servicio: number
  profit_porcentaje: number
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

// Producto con datos nested para listados
export interface ProductoList extends Producto {
  categoria_nombre?: string
  proveedor_nombre?: string
  margen_ganancia: number
  stock_bajo: boolean
}

// Producto con objetos completos nested para detalle
export interface ProductoDetail extends Producto {
  categoria_data?: CategoriaProducto
  proveedor_data?: Proveedor
  margen_ganancia: number
  stock_bajo: boolean
}

export enum TipoMovimiento {
  ENTRADA = 'ENTRADA',
  SALIDA = 'SALIDA',
  AJUSTE = 'AJUSTE',
  TRANSFERENCIA_IN = 'TRANSFERENCIA_IN',
  TRANSFERENCIA_OUT = 'TRANSFERENCIA_OUT',
}

export interface MovimientoInventario {
  id: number
  producto: number
  producto_nombre: string
  tipo: TipoMovimiento
  cantidad: number
  stock_anterior: number
  stock_nuevo: number
  motivo: string
  notas: string
  costo_unitario?: number
  precio_unitario?: number
  usuario?: number
  usuario_nombre?: string
  monto_total: number
  creado_en: string
}

// ==================== FINANCIAL SYSTEM TYPES ====================
// Updated to match new English-code backend models

export enum CategoryType {
  INCOME = 'INCOME',
  EXPENSE = 'EXPENSE',
}

export enum TransactionType {
  INCOME_SERVICE = 'INCOME_SERVICE',
  INCOME_PRODUCT = 'INCOME_PRODUCT',
  INCOME_OTHER = 'INCOME_OTHER',
  EXPENSE = 'EXPENSE',
}

export enum PaymentMethod {
  CASH = 'CASH',
  BANK_TRANSFER = 'BANK_TRANSFER',
  DEBIT_CARD = 'DEBIT_CARD',
  CREDIT_CARD = 'CREDIT_CARD',
  MERCADOPAGO = 'MERCADOPAGO',
  OTHER = 'OTHER',
}

/**
 * Transaction Category - Hierarchical structure (2 levels max)
 */
export interface TransactionCategory {
  id: number
  branch: number
  name: string
  type: CategoryType
  type_display: string
  description: string
  color: string
  icon: string
  parent_category: number | null
  parent_category_name: string | null
  is_active: boolean
  is_system_category: boolean
  order: number
  subcategories?: TransactionCategoryList[]
  transaction_count?: number
  full_path: string
  created_at: string
  updated_at: string
}

/**
 * Lightweight version for dropdowns and selects
 */
export interface TransactionCategoryList {
  id: number
  name: string
  type: CategoryType
  type_display: string
  color: string
  icon: string
  is_active: boolean
  is_system_category: boolean
  parent_category: number | null
  subcategory_count: number
  full_path: string
}

/**
 * Financial Transaction
 */
export interface Transaction {
  id: number
  branch: number
  category: number
  category_name: string
  category_color: string
  client: number | null
  client_name: string | null
  appointment: number | null
  product: number | null
  inventory_movement: number | null
  type: TransactionType
  type_display: string
  amount: number
  signed_amount: number
  payment_method: PaymentMethod
  payment_method_display: string
  date: string
  description: string
  notes: string
  receipt_number: string
  receipt_file: string | null
  auto_generated: boolean
  registered_by: number | null
  registered_by_name: string | null
  edited_by: number | null
  is_income: boolean
  is_expense: boolean
  can_be_edited: boolean
  can_be_deleted: boolean
  created_at: string
  updated_at: string
}

/**
 * Lightweight version for list views
 */
export interface TransactionList {
  id: number
  type: TransactionType
  type_display: string
  category_name: string
  amount: number
  signed_amount: number
  payment_method_display: string
  date: string
  description: string
  client_name: string | null
  auto_generated: boolean
  created_at: string
}

/**
 * Account Receivable (Cuentas por Cobrar)
 */
export interface AccountReceivable {
  id: number
  client: number
  client_name: string
  branch: number
  branch_name: string
  appointment: number | null
  total_amount: number
  paid_amount: number
  pending_amount: number
  issue_date: string
  due_date: string
  full_payment_date: string | null
  description: string
  notes: string
  is_paid: boolean
  is_overdue: boolean
  created_at: string
  updated_at: string
}

/**
 * Financial Summary Response
 */
export interface FinancialSummary {
  income: {
    total: number
    count: number
  }
  expense: {
    total: number
    count: number
  }
  balance: number
  profit_margin: number
}

/**
 * Transaction by Category Response
 */
export interface TransactionByCategory {
  category__id: number
  category__name: string
  category__color: string
  type: TransactionType
  total_amount: number
  transaction_count: number
}

/**
 * Transaction by Payment Method Response
 */
export interface TransactionByPaymentMethod {
  payment_method: PaymentMethod
  payment_method_display: string
  total_amount: number
  transaction_count: number
}

/**
 * Accounts Receivable Summary Response
 */
export interface AccountsReceivableSummary {
  total_owed: number
  total_paid: number
  total_pending: number
  overdue_count: number
  paid_count: number
  pending_count: number
}

// ==================== LEGACY TYPES (for backwards compatibility) ====================
// TODO: Remove these after migrating all components to new types

export enum TipoTransaccion {
  INGRESO_SERVICIO = 'INCOME_SERVICE',
  INGRESO_PRODUCTO = 'INCOME_PRODUCT',
  INGRESO_OTRO = 'INCOME_OTHER',
  GASTO_SUELDO = 'EXPENSE',
  GASTO_ALQUILER = 'EXPENSE',
  GASTO_INSUMO = 'EXPENSE',
  GASTO_SERVICIO = 'EXPENSE',
  GASTO_MARKETING = 'EXPENSE',
  GASTO_OTRO = 'EXPENSE',
}

export enum MetodoPago {
  EFECTIVO = 'CASH',
  TRANSFERENCIA = 'BANK_TRANSFER',
  TARJETA_DEBITO = 'DEBIT_CARD',
  TARJETA_CREDITO = 'CREDIT_CARD',
  MERCADOPAGO = 'MERCADOPAGO',
  OTRO = 'OTHER',
}

/** @deprecated Use Transaction instead */
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
