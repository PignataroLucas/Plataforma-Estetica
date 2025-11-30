import { PaymentMethod, TransactionType } from './models'

/**
 * Mi Caja - Employee Point of Sale System Types
 * Simplified transaction views and operations for employees
 */

// ==================== TRANSACTION TYPES ====================

/**
 * Simplified transaction view for Mi Caja
 */
export interface TransaccionMiCaja {
  id: number
  type: TransactionType
  amount: number | string
  payment_method: PaymentMethod
  date: string
  description: string
  created_by_nombre: string | null
  cliente_nombre: string | null
  concepto: string
  created_at: string
}

// ==================== REQUEST/RESPONSE TYPES ====================

/**
 * Request to charge a completed appointment
 */
export interface CobrarTurnoRequest {
  turno_id: number
  amount: number
  payment_method: PaymentMethod
  notas?: string
}

/**
 * Response from cobrar-turno endpoint
 */
export interface CobrarTurnoResponse {
  success: boolean
  message: string
  transaction: TransaccionMiCaja
}

/**
 * Request to sell a product
 */
export interface VenderProductoRequest {
  producto_id: number
  cantidad: number
  cliente_id: number
  payment_method: PaymentMethod
  descuento_porcentaje?: number
}

/**
 * Response from vender-producto endpoint
 */
export interface VenderProductoResponse {
  success: boolean
  message: string
  transaction: TransaccionMiCaja
  producto: {
    id: number
    nombre: string
    stock_restante: number
  }
}

/**
 * Item for unified sale (product or service)
 */
export interface VentaUnificadaItem {
  tipo: 'producto' | 'servicio'
  producto_id?: number
  turno_id?: number
  cantidad: number
  descuento_porcentaje: number
}

/**
 * Request for unified sale (multiple items)
 */
export interface VentaUnificadaRequest {
  items: VentaUnificadaItem[]
  cliente_id: number
  payment_method: PaymentMethod
  notas?: string
}

/**
 * Response from venta-unificada endpoint
 */
export interface VentaUnificadaResponse {
  success: boolean
  message: string
  transactions: TransaccionMiCaja[]
  productos_actualizados: Array<{
    id: number
    nombre: string
    stock_restante: number
  }>
  total_items: number
  total_monto: number
}

/**
 * Unpaid appointment (pending payment)
 */
export interface TurnoPendienteCobro {
  id: number
  cliente: string
  servicio: string
  monto: number | string
  fecha: string
  hora: string
  estado_pago: string
}

/**
 * Response from turnos-pendientes-cobro endpoint
 */
export interface TurnosPendientesResponse {
  count: number
  turnos: TurnoPendienteCobro[]
}

/**
 * Daily summary for current employee
 */
export interface ResumenDiario {
  fecha: string
  total: number | string
  cantidad_transacciones: number
  por_metodo: Record<string, number | string>
  tiene_cierre: boolean
}

/**
 * Response from mis-transacciones endpoint
 */
export interface MisTransaccionesResponse {
  fecha: string
  empleado: {
    id: number
    nombre: string
  }
  resumen: {
    total: number | string
    cantidad_transacciones: number
    por_metodo: Record<string, number | string>
  }
  transacciones: TransaccionMiCaja[]
}

// ==================== CASH REGISTER CLOSING ====================

/**
 * Cash register closing (Cierre de Caja)
 */
export interface CierreCaja {
  id: number
  empleado: number
  empleado_nombre: string
  sucursal: number
  fecha: string
  total_sistema: number | string
  efectivo_contado: number | string
  diferencia: number | string
  desglose_metodos: Record<string, number | string>
  notas: string
  tiene_diferencia: boolean
  diferencia_significativa: boolean
  cerrado_en: string
}

/**
 * Request to create cash register closing
 */
export interface CierreCajaRequest {
  fecha: string
  efectivo_contado: number
  notas?: string
}

/**
 * Response from cierre-caja endpoint
 */
export interface CierreCajaResponse {
  success: boolean
  message: string
  cierre: CierreCaja
  alerta: boolean
}

// ==================== PAYMENT METHOD DISPLAY ====================

/**
 * Helper to get payment method display name
 */
export const PAYMENT_METHOD_LABELS: Record<PaymentMethod, string> = {
  [PaymentMethod.CASH]: 'Efectivo',
  [PaymentMethod.BANK_TRANSFER]: 'Transferencia',
  [PaymentMethod.DEBIT_CARD]: 'Débito',
  [PaymentMethod.CREDIT_CARD]: 'Crédito',
  [PaymentMethod.MERCADOPAGO]: 'MercadoPago',
  [PaymentMethod.OTHER]: 'Otro'
}

/**
 * Helper to get transaction type display name
 */
export const TRANSACTION_TYPE_LABELS: Record<TransactionType, string> = {
  [TransactionType.INCOME_SERVICE]: 'Servicio',
  [TransactionType.INCOME_PRODUCT]: 'Producto',
  [TransactionType.INCOME_OTHER]: 'Otro Ingreso',
  [TransactionType.EXPENSE]: 'Gasto'
}
