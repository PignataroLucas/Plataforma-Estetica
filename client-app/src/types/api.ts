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
