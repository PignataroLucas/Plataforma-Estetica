/**
 * Cuánto vende la app de las clientas (COMPRA_EN_APP_SPEC.md §5.7).
 *
 * Es la sección que responde si el proyecto valió la pena. Dos decisiones de
 * presentación que vienen del spec y no del gusto:
 *
 * 1. **El ticket promedio se muestra comparado, no solo.** "Cuánto vendió la
 *    app" no distingue las compras que el descuento trajo de las que iban a
 *    pasar igual y solo le costaron margen al centro. La comparación sí.
 * 2. **Los cupones sin usar tienen su propio lugar.** Cada uno es una clienta
 *    que tocó "Comprar" y no terminó. Es la única métrica de este tablero que
 *    Tienda Nube no puede dar: allá el cupón no existe hasta que se usa.
 */

interface Resumen {
  app: {
    ventas: number;
    facturado: number;
    ticket_promedio: number;
    descuento_otorgado: number;
  };
  resto: { ventas: number; facturado: number; ticket_promedio: number };
  participacion_app: number;
}

interface Producto {
  producto_id: number;
  producto: string;
  ventas: number;
  facturado: number;
}

interface Clienta {
  cliente_id: number;
  cliente: string;
  compras: number;
  gastado: number;
}

interface Cupones {
  emitidos: number;
  usados: number;
  sin_usar: number;
  conversion: number;
}

interface VentasAppSectionProps {
  data: {
    resumen: Resumen;
    productos: Producto[];
    clientas: Clienta[];
    cupones: Cupones;
  } | null;
  loading?: boolean;
}

const pesos = (valor: number) =>
  `$${valor.toLocaleString('es-AR', { maximumFractionDigits: 0 })}`;

export default function VentasAppSection({ data, loading }: VentasAppSectionProps) {
  if (loading || !data) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-5 bg-gray-200 rounded w-1/3 mb-6"></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="h-20 bg-gray-100 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  const { resumen, productos, clientas, cupones } = data;
  const sinVentas = resumen.app.ventas === 0;

  // El ticket de la app contra el del resto, en porcentaje. Es el número que
  // dice si el descuento trae compras más grandes o solo más baratas.
  const diferenciaTicket =
    resumen.resto.ticket_promedio > 0
      ? ((resumen.app.ticket_promedio - resumen.resto.ticket_promedio) /
          resumen.resto.ticket_promedio) *
        100
      : 0;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-baseline justify-between mb-1">
        <h2 className="text-lg font-semibold text-gray-900">Ventas desde la app</h2>
        <span className="text-sm text-gray-500">
          {resumen.participacion_app.toFixed(1)}% de lo vendido online
        </span>
      </div>
      <p className="text-sm text-gray-500 mb-6">
        Una venta es de la app cuando llega con un cupón que emitió la app.
      </p>

      {sinVentas && (
        <div className="bg-gray-50 border border-gray-200 rounded-md p-4 mb-6">
          <p className="text-sm text-gray-600">
            Todavía no volvió ninguna venta con un cupón de la app. Los cupones
            emitidos se ven más abajo: son las compras que se empezaron.
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <Metrica titulo="Facturado por la app" valor={pesos(resumen.app.facturado)} />
        <Metrica titulo="Ventas" valor={resumen.app.ventas.toLocaleString('es-AR')} />
        <Metrica
          titulo="Ticket promedio"
          valor={pesos(resumen.app.ticket_promedio)}
          nota={
            resumen.app.ventas > 0 && resumen.resto.ventas > 0
              ? `${diferenciaTicket >= 0 ? '+' : ''}${diferenciaTicket.toFixed(
                  0,
                )}% vs ${pesos(resumen.resto.ticket_promedio)} del resto`
              : undefined
          }
          notaColor={diferenciaTicket >= 0 ? 'text-green-600' : 'text-amber-600'}
        />
        <Metrica
          titulo="Descuento otorgado"
          valor={pesos(resumen.app.descuento_otorgado)}
          nota="lo que costó el incentivo"
        />
      </div>

      {/* Los cupones cuentan otra historia: cuántas compras se empezaron. */}
      <div className="border border-gray-200 rounded-md p-4 mb-8">
        <div className="flex items-baseline justify-between mb-3">
          <h3 className="text-sm font-medium text-gray-700">
            Compras empezadas desde la app
          </h3>
          <span className="text-sm font-semibold text-gray-900">
            {cupones.conversion.toFixed(0)}% se completaron
          </span>
        </div>
        <div className="grid grid-cols-3 gap-4 text-center">
          <Chico titulo="Cupones emitidos" valor={cupones.emitidos} />
          <Chico titulo="Terminaron en compra" valor={cupones.usados} />
          <Chico
            titulo="Quedaron sin usar"
            valor={cupones.sin_usar}
            color="text-amber-600"
          />
        </div>
        <p className="text-xs text-gray-500 mt-3">
          Cada cupón se emite al tocar “Comprar”. Los que quedan sin usar son
          carritos abandonados en el checkout.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Tabla
          titulo="Productos que vende la app"
          vacio="Ninguno todavía"
          filas={productos.map((p) => ({
            clave: p.producto_id,
            nombre: p.producto,
            detalle: `${p.ventas} ${p.ventas === 1 ? 'venta' : 'ventas'}`,
            monto: pesos(p.facturado),
          }))}
        />
        <Tabla
          titulo="Clientas que compran por la app"
          vacio="Ninguna todavía"
          filas={clientas.map((c) => ({
            clave: c.cliente_id,
            nombre: c.cliente,
            detalle: `${c.compras} ${c.compras === 1 ? 'compra' : 'compras'}`,
            monto: pesos(c.gastado),
          }))}
        />
      </div>
    </div>
  );
}

function Metrica({
  titulo,
  valor,
  nota,
  notaColor = 'text-gray-500',
}: {
  titulo: string;
  valor: string;
  nota?: string;
  notaColor?: string;
}) {
  return (
    <div className="border border-gray-200 rounded-md p-4">
      <p className="text-sm text-gray-600 mb-1">{titulo}</p>
      <p className="text-2xl font-bold text-gray-900">{valor}</p>
      {nota && <p className={`text-xs mt-1 ${notaColor}`}>{nota}</p>}
    </div>
  );
}

function Chico({
  titulo,
  valor,
  color = 'text-gray-900',
}: {
  titulo: string;
  valor: number;
  color?: string;
}) {
  return (
    <div>
      <p className={`text-2xl font-bold ${color}`}>{valor.toLocaleString('es-AR')}</p>
      <p className="text-xs text-gray-600 mt-1">{titulo}</p>
    </div>
  );
}

function Tabla({
  titulo,
  vacio,
  filas,
}: {
  titulo: string;
  vacio: string;
  filas: { clave: number; nombre: string; detalle: string; monto: string }[];
}) {
  return (
    <div>
      <h3 className="text-sm font-medium text-gray-700 mb-3">{titulo}</h3>
      {filas.length === 0 ? (
        <p className="text-sm text-gray-400 py-4">{vacio}</p>
      ) : (
        <ul className="divide-y divide-gray-100">
          {filas.map((f) => (
            <li key={f.clave} className="flex items-center justify-between py-2">
              <div className="min-w-0 pr-4">
                <p className="text-sm text-gray-900 truncate">{f.nombre}</p>
                <p className="text-xs text-gray-500">{f.detalle}</p>
              </div>
              <span className="text-sm font-medium text-gray-900 whitespace-nowrap">
                {f.monto}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
