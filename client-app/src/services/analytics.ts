/**
 * Medición de uso con Google Analytics para Firebase.
 *
 * Todo evento de la app pasa por acá: las pantallas llaman a `analytics.*` con
 * objetos del dominio y este módulo los traduce al formato de GA4. Así los
 * nombres de evento y de parámetro viven en un solo lugar —GA4 acepta en
 * silencio un parámetro mal escrito y después el evento no aparece en ningún
 * reporte— y cambiar de proveedor sería tocar un solo archivo.
 *
 * Para lo que tiene evento recomendado de GA4 (`login`, `sign_up`, `view_item`,
 * `add_to_cart`, `begin_checkout`, `purchase`) se usa ese, y no uno propio: son
 * los que alimentan solos los informes de comercio y el embudo de compra.
 *
 * **Se carga con `require()` y solo donde existe**, igual que
 * `notificacionesNativas.ts`: Expo Go no trae el módulo nativo de Firebase, y en
 * web no hay app registrada en Firebase. En los dos casos cada llamada es un
 * no-op. Medir es accesorio: un error acá nunca puede cortar un flujo.
 *
 * Qué NO se manda: ni email, ni nombre, ni teléfono. El usuario se identifica
 * con el id numérico de la cuenta, que no dice nada fuera de nuestra base. El
 * ID de publicidad tampoco: está apagado en `firebase.json` y el permiso
 * `AD_ID` se bloquea en `app.json`.
 */
import { isRunningInExpoGo } from 'expo';
import { Platform } from 'react-native';

// Solo tipos: TypeScript lo borra al compilar, no genera require.
import type * as FirebaseAnalytics from '@react-native-firebase/analytics';

import type { ProductoPublico, ServicioPublico, TurnoApp } from '@/types/api';
import { aNumero } from '@/utils/precios';

type Modulo = typeof FirebaseAnalytics;
type Item = FirebaseAnalytics.Item;

const MONEDA = 'ARS';

const DISPONIBLE = Platform.OS !== 'web' && !isRunningInExpoGo();

// `undefined` = todavía no se intentó; `null` = se intentó y no está.
let sdk: { mod: Modulo; instancia: FirebaseAnalytics.Analytics } | null | undefined;

function cargar() {
  if (sdk !== undefined) return sdk;
  if (!DISPONIBLE) {
    sdk = null;
    return sdk;
  }
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const mod = require('@react-native-firebase/analytics') as Modulo;
    sdk = { mod, instancia: mod.getAnalytics() };
  } catch (error) {
    console.warn('[analytics] No se pudo cargar Firebase Analytics:', error);
    sdk = null;
  }
  return sdk;
}

/** Corre la llamada si hay SDK y se traga cualquier error, sincrónico o no. */
function medir(fn: (mod: Modulo, instancia: FirebaseAnalytics.Analytics) => unknown): void {
  const s = cargar();
  if (!s) return;
  try {
    const r = fn(s.mod, s.instancia);
    if (r instanceof Promise) r.catch((e) => console.warn('[analytics]', e));
  } catch (error) {
    console.warn('[analytics]', error);
  }
}

/** Un evento propio. Nombre en snake_case y de hasta 40 caracteres (límite de GA4). */
function evento(nombre: string, params?: Record<string, string | number>): void {
  medir((mod, a) => mod.logEvent(a, nombre, params));
}

/** Una línea del carrito, tal como la guarda `stores/carrito.ts`. */
export interface LineaMedida {
  productoId: number;
  nombre: string;
  marca: string;
  precio: string;
  cantidad: number;
}

function itemDeLinea(linea: LineaMedida): Item {
  return {
    item_id: String(linea.productoId),
    item_name: linea.nombre,
    item_brand: linea.marca || undefined,
    item_category: 'producto',
    price: aNumero(linea.precio),
    quantity: linea.cantidad,
  };
}

function totalDe(lineas: LineaMedida[]): number {
  return lineas.reduce((suma, l) => suma + aNumero(l.precio) * l.cantidad, 0);
}

export const analytics = {
  /**
   * Ata los eventos a la cuenta, para contar personas y no teléfonos. `null` al
   * cerrar sesión: si no, la próxima que entre en el mismo teléfono hereda la
   * identidad de la anterior.
   */
  identificar(usuarioId: number | null): void {
    medir((mod, a) => mod.setUserId(a, usuarioId === null ? null : String(usuarioId)));
  },

  /**
   * Pantalla vista. La ruta llega con la forma del archivo (`/producto/[id]`) y
   * no con el id real: si no, cada producto sería una pantalla distinta en los
   * informes. El reporte automático de pantallas está apagado en
   * `firebase.json` porque en React Native ve una sola Activity.
   */
  pantalla(ruta: string): void {
    medir((mod, a) => mod.logEvent(a, 'screen_view', { screen_name: ruta, screen_class: ruta }));
  },

  inicioSesion(): void {
    medir((mod, a) => mod.logEvent(a, 'login', { method: 'email' }));
  },

  /** `codigo`: la vinculó el centro con una invitación. `directo`: se registró sola. */
  registro(metodo: 'codigo' | 'directo'): void {
    medir((mod, a) => mod.logEvent(a, 'sign_up', { method: metodo }));
  },

  verProducto(producto: ProductoPublico): void {
    // El que ve la clienta: si está en oferta, el de oferta.
    const precio = aNumero(
      producto.en_oferta && producto.precio_oferta ? producto.precio_oferta : producto.precio,
    );
    medir((mod, a) =>
      mod.logEvent(a, 'view_item', {
        currency: MONEDA,
        value: precio,
        items: [
          {
            item_id: String(producto.id),
            item_name: producto.nombre,
            item_brand: producto.marca || undefined,
            item_category: 'producto',
            price: precio,
          },
        ],
      }),
    );
  },

  /** Mismo evento que el producto, separado por `item_category`. */
  verServicio(servicio: ServicioPublico): void {
    medir((mod, a) =>
      mod.logEvent(a, 'view_item', {
        items: [
          {
            item_id: `servicio-${servicio.id}`,
            item_name: servicio.nombre,
            item_category: 'servicio',
          },
        ],
      }),
    );
  },

  agregarAlCarrito(linea: LineaMedida): void {
    medir((mod, a) =>
      mod.logEvent(a, 'add_to_cart', {
        currency: MONEDA,
        value: totalDe([linea]),
        items: [itemDeLinea(linea)],
      }),
    );
  },

  /** Tocó "Comprar": entra al checkout de Tienda Nube. */
  iniciarCompra(lineas: LineaMedida[]): void {
    medir((mod, a) =>
      mod.logEvent(a, 'begin_checkout', {
        currency: MONEDA,
        value: totalDe(lineas),
        items: lineas.map(itemDeLinea),
      }),
    );
  },

  /**
   * Tienda Nube mostró la página de éxito. `total` es lo que pagó, ya con el
   * descuento. No hay número de pedido del lado de la app: el cupón es único
   * por compra y sirve de `transaction_id` cuando existe.
   */
  compraTerminada(lineas: LineaMedida[], total: string, cupon: string | null): void {
    medir((mod, a) =>
      mod.logEvent(a, 'purchase', {
        currency: MONEDA,
        value: aNumero(total),
        ...(cupon ? { transaction_id: cupon, coupon: cupon } : {}),
        items: lineas.map(itemDeLinea),
      }),
    );
  },

  /** `estado` separa los que quedaron esperando aprobación de los confirmados. */
  turnoReservado(turno: TurnoApp): void {
    evento('reservar_turno', {
      servicio_id: turno.servicio,
      servicio_nombre: turno.servicio_nombre,
      estado: turno.estado,
    });
  },

  turnoCancelado(turno: TurnoApp): void {
    evento('cancelar_turno', {
      servicio_id: turno.servicio,
      servicio_nombre: turno.servicio_nombre,
    });
  },

  /** Tocó un aviso push. `evento` es la clave del catálogo del backend. */
  notificacionAbierta(clave: string): void {
    evento('abrir_notificacion', { evento: clave });
  },
};
