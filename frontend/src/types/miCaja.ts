import { PaymentMethod, TransactionType } from './models'

/**
 * Mi Caja - Employee Point of Sale System Types
 */

// ==================== TRANSACTION TYPES ====================

export interface TransaccionMiCaja {
  id: number
  type: TransactionType
  amount: number | string
  payment_method: PaymentMethod
  date: string
  description: string
  notes: string
  created_by_nombre: string | null
  cliente_nombre: string | null
  concepto: string
  created_at: string
}

// ==================== UNIFIED SALE ====================

export interface VentaUnificadaItem {
  tipo: 'producto' | 'servicio' | 'servicio_directo'
  producto_id?: number
  turno_id?: number
  servicio_id?: number
  cantidad: number
  precio_unitario?: number
  descuento_porcentaje: number
}

export interface VentaUnificadaRequest {
  items: VentaUnificadaItem[]
  cliente_id: number | null
  payment_method: PaymentMethod
  notas?: string
}

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

// ==================== EDIT TRANSACTION ====================

export interface EditarTransaccionRequest {
  transaccion_id: number
  amount?: number
  payment_method?: PaymentMethod
  notas?: string
  cliente_id?: number | null
}

export interface EditarTransaccionResponse {
  success: boolean
  message: string
  transaction: TransaccionMiCaja
}

// ==================== DELETE TRANSACTION ====================

export interface EliminarTransaccionRequest {
  transaccion_id: number
  motivo: string
}

export interface EliminarTransaccionResponse {
  success: boolean
  message: string
}

// ==================== PENDING APPOINTMENTS ====================

export interface TurnoPendienteCobro {
  id: number
  cliente: string
  servicio: string
  profesional: string
  monto: number | string
  monto_total: number | string
  monto_sena: number | string
  fecha: string
  hora: string
  estado_pago: string
}

export interface TurnosPendientesResponse {
  count: number
  turnos: TurnoPendienteCobro[]
}

// ==================== DAILY SUMMARY ====================

export interface ResumenDiario {
  fecha: string
  total: number | string
  cantidad_transacciones: number
  por_metodo: Record<string, number | string>
  tiene_cierre: boolean
}

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

export interface CierreCajaRequest {
  fecha: string
  efectivo_contado: number
  notas?: string
}

export interface CierreCajaResponse {
  success: boolean
  message: string
  cierre: CierreCaja
  alerta: boolean
}

// ==================== DISPLAY HELPERS ====================

export const PAYMENT_METHOD_LABELS: Record<PaymentMethod, string> = {
  [PaymentMethod.CASH]: 'Efectivo',
  [PaymentMethod.BANK_TRANSFER]: 'Transferencia',
  [PaymentMethod.DEBIT_CARD]: 'Débito',
  [PaymentMethod.CREDIT_CARD]: 'Crédito',
  [PaymentMethod.MERCADOPAGO]: 'MercadoPago',
  [PaymentMethod.OTHER]: 'Otro'
}

export const TRANSACTION_TYPE_LABELS: Record<TransactionType, string> = {
  [TransactionType.INCOME_SERVICE]: 'Servicio',
  [TransactionType.INCOME_PRODUCT]: 'Producto',
  [TransactionType.INCOME_OTHER]: 'Otro Ingreso',
  [TransactionType.EXPENSE]: 'Gasto'
}
