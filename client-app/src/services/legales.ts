/** Documentos legales: abrirlos y aceptarlos. */
import * as WebBrowser from 'expo-web-browser';

import type { Perfil } from '@/types/api';

import { urlDelSitio } from './config';
import { authPost } from './http';

/** Abre una página legal del backend en el navegador del sistema, sin salir de la app. */
export function abrirDocumento(ruta: string): Promise<unknown> {
  return WebBrowser.openBrowserAsync(urlDelSitio(ruta));
}

/**
 * POST /api/client/legales/aceptar/ — devuelve el perfil ya sin ese pendiente.
 *
 * Manda la versión que la clienta vio: si el documento cambió mientras tanto,
 * el backend la rechaza para que lea la nueva.
 */
export function aceptarLegal(documento: string, version: string): Promise<Perfil> {
  return authPost<Perfil>('/client/legales/aceptar/', { documento, version });
}
