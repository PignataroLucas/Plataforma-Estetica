import { Feather } from '@expo/vector-icons';
import * as Clipboard from 'expo-clipboard';
import { router } from 'expo-router';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { WebView, type WebViewMessageEvent } from 'react-native-webview';

import { AppText } from '@/components/ui/AppText';
import { Button } from '@/components/ui/Button';
import { useCentroActivo } from '@/hooks/useCentroActivo';
import { prepararCompra } from '@/services/compra';
import { useCarritoStore } from '@/stores/carrito';
import { colors, radius, spacing } from '@/theme/ame';
import type { CompraPreparada } from '@/types/api';
import { aNumero, formatPorcentaje } from '@/utils/precios';

/**
 * Trozos de URL que indican que Tienda Nube terminó la compra.
 *
 * **Verificado con una compra real el 30/08/2026**: el retorno se detectó y la
 * clienta vio la confirmación de AME, no la página de gracias de Tienda Nube.
 *
 * Lo que falta saber es **cuál de las tres matcheó**. Las otras dos siguen
 * siendo adivinanzas, y una adivinanza de más es peor que de menos: si alguna
 * matchea una URL intermedia del checkout, el WebView se cierra antes de que la
 * clienta pague. Con el dato de una compra hay que dejar solo la buena.
 */
const URLS_DE_EXITO = ['/checkout/v3/success', '/success', '/gracias'];

/**
 * Red de contención, no el camino normal.
 *
 * Lo que decide es el mensaje del script: `cupon-ok` o `cupon-falló`. Este
 * temporizador solo cubre el caso de que el script muera sin avisar.
 *
 * **Tiene que ser más largo que el presupuesto del script**, o la app se rinde
 * mientras el script todavía está trabajando y le muestra el código a una
 * clienta a la que el cupón se le iba a aplicar solo. Ese presupuesto es
 * grande: 15 s para encontrar el link, 8 para el campo y 10 para verificar,
 * por hasta tres intentos.
 *
 * Medido en el emulador: una compra normal tarda **unos 18 segundos** desde
 * "Comprar" hasta el cupón aplicado —dos cargas de página, un pedido por
 * producto y el arranque del checkout de Tienda Nube—. Con los 20 s que había
 * antes, el margen era de dos segundos.
 */
const ESPERA_CUPON_MS = 45000;

/**
 * Checkout de Tienda Nube, dentro del marco de AME.
 *
 * El recorrido es el del §4: se prepara la compra en nuestro backend (que emite
 * el cupón), se arma el carrito del otro lado y se aplica el descuento sin que
 * la clienta escriba nada.
 *
 * Por qué un formulario y no una URL: Tienda Nube **no tiene** una URL que
 * agregue al carrito —probado— y solo acepta un producto por POST. Así que el
 * WebView arranca en un form nuestro que se auto-envía, y el resto de los
 * productos los agrega el script inyectado. Ver §6.6.
 */
export default function CheckoutScreen() {
  const { centroId } = useCentroActivo();
  const items = useCarritoStore((s) => s.items);
  const vaciar = useCarritoStore((s) => s.vaciar);

  const [compra, setCompra] = useState<CompraPreparada | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cuponAplicado, setCuponAplicado] = useState(false);
  const [pedirCupon, setPedirCupon] = useState(false);
  const [copiado, setCopiado] = useState(false);
  // Solo para desarrollo: en qué paso se quedó la inyección del cupón.
  const [pasoFallido, setPasoFallido] = useState<string | null>(null);
  const [listo, setListo] = useState(false);

  useEffect(() => {
    let cancelado = false;
    const lineas = items.map((i) => ({ producto: i.productoId, cantidad: i.cantidad }));

    prepararCompra(lineas, centroId)
      .then((datos) => {
        if (cancelado) return;
        setCompra(datos);
      })
      .catch((e) => {
        if (cancelado) return;
        setError(e?.message ?? 'No pudimos preparar tu compra.');
      });

    return () => {
      cancelado = true;
    };
    // Se prepara una sola vez: cada corrida emite un cupón nuevo.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /**
   * El cupón no se puede pre-aplicar por URL —probado contra la tienda real—,
   * así que se escribe en el campo del checkout. Si en unos segundos no
   * apareció el descuento, se le muestra el código a la clienta en vez de
   * dejarla pagar el precio de lista, que es la trampa del §6.1.
   */
  useEffect(() => {
    if (!compra?.cupon || cuponAplicado) return;
    const t = setTimeout(() => setPedirCupon(true), ESPERA_CUPON_MS);
    return () => clearTimeout(t);
  }, [compra, cuponAplicado]);

  const onMessage = useCallback((event: WebViewMessageEvent) => {
    try {
      const dato = JSON.parse(event.nativeEvent.data);
      if (dato.tipo === 'cupon-ok') {
        setCuponAplicado(true);
        setPedirCupon(false);
      }
      if (dato.tipo === 'cupon-falló') {
        setPedirCupon(true);
        setPasoFallido(dato.paso || 'desconocido');
      }
    } catch {
      // Un mensaje que no entendemos no puede tumbar el checkout.
    }
  }, []);

  const onNavegacion = useCallback(
    (estado: { url: string }) => {
      if (listo) return;
      if (URLS_DE_EXITO.some((u) => estado.url.includes(u))) {
        setListo(true);
        vaciar();
      }
    },
    [listo, vaciar],
  );

  const copiar = async () => {
    if (!compra?.cupon) return;
    await Clipboard.setStringAsync(compra.cupon.codigo);
    setCopiado(true);
  };

  const cerrar = () => {
    if (router.canGoBack()) router.back();
    else router.replace('/tienda');
  };

  if (listo) return <Confirmacion />;

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
      <View style={styles.header}>
        <Pressable onPress={cerrar} hitSlop={12} style={styles.icono} accessibilityRole="button">
          <Feather name="x" size={20} color={colors.ink} />
        </Pressable>
        <AppText variant="section">Tu compra</AppText>
        {/* El candado del §5.5: dice que se paga en un sitio seguro, sin barra
            de direcciones que lo demuestre. */}
        <View style={styles.icono}>
          <Feather name="lock" size={16} color={colors.muted} />
        </View>
      </View>

      {error ? (
        <View style={styles.centro}>
          <AppText variant="body" color={colors.muted} style={styles.centrado}>
            {error}
          </AppText>
          <Button label="Volver" variant="ghost" onPress={cerrar} />
        </View>
      ) : !compra ? (
        <View style={styles.centro}>
          <ActivityIndicator color={colors.muted} />
          <AppText variant="meta">Preparando tu compra…</AppText>
        </View>
      ) : (
        <>
          {/*
            El WebView se monta y trabaja detrás de esta cortina. Sin ella, la
            clienta ve el total SIN descuento durante los segundos que tarda
            aplicar el cupón —el checkout de TN carga, el script busca el campo,
            escribe y confirma— y después lo ve bajar solo. Es una versión suave
            del §6.1: mostrarle un precio que no es el que va a pagar. Acá baja,
            así que no pierde la venta, pero la acostumbra a ver el número alto
            primero, y el día que el cupón falle no va a notar que no bajó.

            Se levanta cuando el descuento está aplicado, o cuando se agota la
            espera y hay que mostrarle el código para que lo pegue a mano. Nunca
            queda trabada: el temporizador de `pedirCupon` la destapa igual.
          */}
          {pedirCupon && compra.cupon ? (
            <View style={styles.aviso}>
              <AppText variant="meta" style={styles.avisoTxt}>
                Ingresá este código en “Agregar cupón de descuento” para tu{' '}
                {formatPorcentaje(aNumero(compra.cupon.porcentaje))} off:
              </AppText>
              <Pressable onPress={copiar} style={styles.codigo} accessibilityRole="button">
                <AppText variant="price" style={styles.codigoTxt}>
                  {compra.cupon.codigo}
                </AppText>
                <Feather name={copiado ? 'check' : 'copy'} size={14} color={colors.ink} />
              </Pressable>
              {__DEV__ && pasoFallido ? (
                <AppText variant="meta">se cortó en: {pasoFallido}</AppText>
              ) : null}
            </View>
          ) : null}

          {/*
            El WebView va dentro de un contenedor propio para que la cortina
            pueda taparlo sin desmontarlo: tiene que seguir cargando, agregando
            al carrito y aplicando el cupón por detrás.
          */}
          <View style={styles.lienzo}>
            <Tienda compra={compra} onMessage={onMessage} onNavegacion={onNavegacion} />
            {compra.cupon && !cuponAplicado && !pedirCupon ? (
              <Preparando porcentaje={compra.cupon.porcentaje} />
            ) : null}
          </View>
        </>
      )}
    </SafeAreaView>
  );
}

function Tienda({
  compra,
  onMessage,
  onNavegacion,
}: {
  compra: CompraPreparada;
  onMessage: (e: WebViewMessageEvent) => void;
  onNavegacion: (e: { url: string }) => void;
}) {
  const html = useMemo(() => paginaDeEntrada(compra), [compra]);
  const script = useMemo(() => guion(compra), [compra]);

  return (
    <WebView
      source={{ html, baseUrl: origenDe(compra.checkout.url) }}
      originWhitelist={['*']}
      injectedJavaScript={script}
      onMessage={onMessage}
      onNavigationStateChange={onNavegacion}
      /*
        Sin sesión persistente, y es lo que arregla el bug feo: el carrito de
        Tienda Nube vive en una cookie que sobrevive entre compras y entre
        reinicios de la app, así que cada "Comprar" apilaba sobre lo anterior.
        Vaciarlo desde adentro no es viable —`quantity[x]=0` no borra nada, y el
        "Borrar" del tema llama a una función interna de ellos que recarga la
        página—, así que se arranca sin cookies y el carrito nace vacío.

        Las cookies siguen funcionando dentro de la compra: incognito no las
        desactiva, solo no las guarda al cerrar.
      */
      incognito
      thirdPartyCookiesEnabled
      startInLoadingState
      style={styles.web}
    />
  );
}

/**
 * La cortina que tapa el checkout mientras se aplica el cupón.
 *
 * Dice el porcentaje a propósito: convierte una espera muda en una promesa
 * concreta, y cuando se levanta la clienta ya sabe qué número tiene que ver.
 *
 * Los segundos que tapa son inherentes al camino, no un defecto que se pueda
 * optimizar: son dos cargas de página, un pedido por producto —Tienda Nube
 * descarta los que van juntos—, el arranque de su checkout, y recién ahí la
 * escritura del cupón.
 */
function Preparando({ porcentaje }: { porcentaje: string }) {
  return (
    <View style={styles.cortina}>
      <ActivityIndicator color={colors.muted} />
      <AppText variant="section">Preparando tu compra</AppText>
      <AppText variant="body" color={colors.muted} style={styles.centrado}>
        Estamos aplicando tu {formatPorcentaje(aNumero(porcentaje))} de descuento.
      </AppText>
    </View>
  );
}

/**
 * Sin monto, y es a propósito.
 *
 * Acá se mostraba el total que calculó el backend al preparar la compra, y ese
 * número **no incluye el envío**: la clienta lo elige adentro del WebView,
 * después. En la primera compra real la app dijo $10.625 y Tienda Nube cobró
 * $10.675 (§6.1).
 *
 * Afirmar un número que no controlamos es peor que no afirmar ninguno, sobre
 * todo cuando el nuestro siempre va a ser **menor** que el verdadero. El
 * detalle con el total real se lo manda Tienda Nube por mail igual.
 */
function Confirmacion() {
  return (
    <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
      <View style={styles.centro}>
        <Feather name="check-circle" size={40} color={colors.ink} />
        <AppText variant="title">¡Listo!</AppText>
        <AppText variant="body" style={styles.centrado}>
          Recibimos tu compra. Te llega el detalle por mail.
        </AppText>
        <Button label="Volver a la tienda" onPress={() => router.replace('/tienda')} />
      </View>
    </SafeAreaView>
  );
}

/** Solo el origen: el `baseUrl` del WebView tiene que ser el de la tienda. */
function origenDe(url: string): string {
  const m = url.match(/^https?:\/\/[^/]+/);
  return m ? m[0] : url;
}

/**
 * La página que abre el WebView: entra al carrito de la tienda y nada más.
 *
 * No agrega productos: de eso se ocupa el script una vez parado en el dominio
 * de la tienda, que es donde puede postear contra `/comprar/`.
 */
function paginaDeEntrada(compra: CompraPreparada): string {
  return `<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{margin:0;height:100vh;display:flex;align-items:center;justify-content:center;background:${colors.ivory};font-family:-apple-system,system-ui,sans-serif;color:${colors.muted};font-size:13px}</style>
</head><body>
<p>Abriendo tu carrito…</p>
<script>location.replace(${JSON.stringify(compra.checkout.url)});</script>
</body></html>`;
}

/**
 * Lo que corre dentro de la tienda, en cada página que carga.
 *
 * Dos trabajos, según dónde esté: terminar de armar el carrito y saltar al
 * checkout, o escribir el cupón. Lo segundo depende del HTML de Tienda Nube y
 * por eso avisa si no pudo: la pantalla le muestra el código a la clienta en
 * lugar de dejarla pagar sin descuento.
 */
function guion(compra: CompraPreparada): string {
  const items = compra.checkout.items;
  const cupon = compra.cupon?.codigo ?? null;

  return `(function(){
  if (window.__ame) return true;
  window.__ame = 1;
  var ITEMS = ${JSON.stringify(items)};
  var CUPON = ${JSON.stringify(cupon)};

  function avisar(tipo, paso){
    if (window.ReactNativeWebView)
      window.ReactNativeWebView.postMessage(JSON.stringify({tipo: tipo, paso: paso || ''}));
  }
  function postear(body){
    return fetch('/comprar/', {
      method: 'POST', credentials: 'include',
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: body
    });
  }
  function esperar(buscar, limite, listo){
    var t0 = Date.now();
    (function loop(){
      var r = buscar();
      if (r) return listo(r);
      if (Date.now() - t0 > limite) return listo(null);
      setTimeout(loop, 300);
    })();
  }

  function agregar(i){
    if (i >= ITEMS.length) {
      // Un POST por producto: Tienda Nube descarta los pares de más.
      return postear('go_to_checkout=1').then(function(r){ location.replace(r.url); });
    }
    var it = ITEMS[i];
    return postear('add_to_cart=' + it.producto_tiendanube + '&quantity=' + it.cantidad)
      .then(function(){ agregar(i + 1); })
      .catch(function(){ agregar(i + 1); });
  }

  function aplicarCupon(intento){
    if (!CUPON) return;
    intento = intento || 1;

    esperar(function(){
      var todos = [].slice.call(document.querySelectorAll('*')).filter(function(e){
        return /^Agregar cup[oó]n de descuento$/i.test((e.textContent || '').trim());
      });
      return todos.length ? todos[todos.length - 1] : null;
    }, 15000, function(link){
      if (!link) return reintentar(intento, 'link');
      link.click();

      esperar(function(){ return document.querySelector('input[name="coupon"]'); }, 8000, function(input){
        if (!input) return reintentar(intento, 'input');

        // El input es de React: sin el setter nativo el valor no llega al
        // estado y el botón manda vacío.
        var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        setter.call(input, CUPON);
        input.dispatchEvent(new Event('input', {bubbles: true}));

        setTimeout(function(){
          var form = input.closest('form');
          var boton = form && form.querySelector('button');
          if (!boton) return reintentar(intento, 'boton');
          boton.click();

          // Se confirma buscando el código y no la frase "Descuento del cupón":
          // en el layout de celular ese resumen viene colapsado detrás de "Ver
          // detalles de mi compra" y el texto no está en la página.
          esperar(function(){
            var txt = document.body.innerText || '';
            return (txt.indexOf(CUPON) !== -1 || /Descuento del cup/i.test(txt)) ? true : null;
          }, 10000, function(ok){
            if (ok) return avisar('cupon-ok');
            reintentar(intento, 'verificacion');
          });
        }, 500);
      });
    });
  }

  /**
   * El checkout es una SPA y a veces el campo tarda o el click cae antes de que
   * React lo escuche, así que se reintenta. Pero **nunca mientras la clienta
   * está escribiendo**: cada intento vuelve a abrir el campo del cupón, eso
   * re-renderiza el formulario, y si está tipeando el mail se le come lo que
   * sigue. Con el foco puesto en otro campo, se espera.
   */
  function reintentar(intento, paso){
    if (intento >= 3) return avisar('cupon-falló', paso);

    var esperas = 0;
    (function cuandoEsteLibre(){
      var activo = document.activeElement;
      var escribiendo = activo && /INPUT|TEXTAREA|SELECT/.test(activo.tagName)
        && activo.name !== 'coupon';

      // Si no suelta el teclado, se abandona: mejor el cartel con el código que
      // pelearle el formulario.
      if (escribiendo && ++esperas > 20) return avisar('cupon-falló', 'ocupada');
      if (escribiendo) return setTimeout(cuandoEsteLibre, 1000);

      aplicarCupon(intento + 1);
    })();
  }

  if (location.pathname.indexOf('/comprar') === 0) agregar(0);
  else if (location.pathname.indexOf('/checkout') === 0) aplicarCupon(1);
})();
true;`;
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.ivory },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.md,
  },
  icono: { width: 40, height: 40, justifyContent: 'center' },
  centro: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.md,
    padding: spacing.xl,
  },
  centrado: { textAlign: 'center', lineHeight: 20 },
  web: { flex: 1 },

  // El WebView y su cortina comparten este espacio; la cortina va encima.
  lienzo: { flex: 1 },
  cortina: {
    // Escrito a mano en vez de `absoluteFill`: los tipos de esta versión no
    // exponen `absoluteFillObject`, y cuatro propiedades no ameritan la duda.
    position: 'absolute',
    top: 0,
    right: 0,
    bottom: 0,
    left: 0,
    // Opaco, no translúcido: la idea es que el precio de atrás no se vea.
    backgroundColor: colors.ivory,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.md,
    padding: spacing.xl,
  },

  aviso: {
    marginHorizontal: spacing.xl,
    marginBottom: spacing.sm,
    padding: spacing.md,
    backgroundColor: colors.blush,
    borderRadius: radius.md,
    gap: spacing.sm,
  },
  avisoTxt: { color: colors.ink, lineHeight: 16 },
  codigo: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    paddingVertical: spacing.sm,
    backgroundColor: colors.card,
    borderRadius: radius.sm,
  },
  codigoTxt: { letterSpacing: 1.5 },
});
