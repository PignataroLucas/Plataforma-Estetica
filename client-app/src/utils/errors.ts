import { ApiError } from '@/services/api';

export interface FormErrors {
  /** Errores por campo (clave = nombre del campo del backend). */
  fields: Record<string, string>;
  /** Error general para el banner, o null si ya se muestra en un campo. */
  general: string | null;
}

/**
 * Traduce el error de una request a errores de formulario.
 *
 * `rendered` son los campos que la pantalla muestra: si el error cae en uno de
 * ellos se pinta inline y no se duplica en el banner. Cualquier otro error
 * (credenciales, campo no visible, red) va al banner para no perderse.
 */
export function toFormErrors(e: unknown, rendered: string[] = []): FormErrors {
  if (e instanceof ApiError) {
    const fields = e.fields ?? {};
    const yaVisibleEnCampo = rendered.some((k) => fields[k]);
    return {
      fields,
      general: yaVisibleEnCampo ? null : e.message || 'Ocurrió un error. Intentá de nuevo.',
    };
  }
  return { fields: {}, general: 'Ocurrió un error inesperado.' };
}
