import { Feather } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';
import { Image } from 'expo-image';
import { router } from 'expo-router';
import { useMemo } from 'react';
import { Pressable, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { AppText } from '@/components/ui/AppText';
import { Button } from '@/components/ui/Button';
import { useCentroActivo } from '@/hooks/useCentroActivo';
import { useDescuentoApp } from '@/hooks/useDescuentoApp';
import { resolveMediaUrl } from '@/services/config';
import { getProductos } from '@/services/public';
import { MAX_POR_PRODUCTO, useCarritoStore, type ItemCarrito } from '@/stores/carrito';
import { colors, radius, spacing } from '@/theme/ame';
import { formatPrecio } from '@/utils/format';
import { aNumero, conDescuento, formatPorcentaje } from '@/utils/precios';

interface Linea extends ItemCarrito {
  /** Precio unitario a mostrar, ya resuelto contra el catálogo fresco. */
  unitario: number;
  subtotal: number;
  /** El catálogo cargó y este producto ya no está: no se va a poder comprar. */
  discontinuado: boolean;
}

/**
 * Carrito de la app.
 *
 * Pantalla de stack y no tab: se entra desde la Tienda o desde la ficha y se
 * sale por donde se vino. Los items viven en el dispositivo (stores/carrito).
 */
export default function CarritoScreen() {
  const { centroId } = useCentroActivo();
  const { porcentaje: descuento } = useDescuentoApp();
  const items = useCarritoStore((s) => s.items);
  const cambiarCantidad = useCarritoStore((s) => s.cambiarCantidad);
  const quitar = useCarritoStore((s) => s.quitar);
  const vaciar = useCarritoStore((s) => s.vaciar);

  /**
   * El carrito guarda el precio de cuando se agregó, pero acá se relee el
   * catálogo y gana el fresco. El precio base lo actualiza el sync de Conto, así
   * que puede haber cambiado entre agregar y comprar (COMPRA_EN_APP_SPEC.md
   * §6.2), y mostrar uno para cobrar otro es la peor forma de perder la venta.
   * Es la misma query que ya trae la Tienda: casi siempre sale del cache.
   */
  const { data } = useQuery({
    queryKey: ['productos', centroId],
    queryFn: () => getProductos(centroId),
  });

  const lineas = useMemo<Linea[]>(() => {
    const frescos = data?.results;
    return items.map((item) => {
      const fresco = frescos?.find((p) => p.id === item.productoId);
      const unitario = aNumero(fresco?.precio ?? item.precio);
      return {
        ...item,
        nombre: fresco?.nombre ?? item.nombre,
        marca: fresco?.marca ?? item.marca,
        foto: fresco ? (fresco.foto_thumb ?? fresco.foto) : item.foto,
        unitario,
        subtotal: unitario * item.cantidad,
        discontinuado: Boolean(frescos) && !fresco,
      };
    });
  }, [items, data]);

  // Lo que ya no está en el catálogo no suma: no se va a poder comprar.
  const subtotal = lineas.reduce((acc, l) => (l.discontinuado ? acc : acc + l.subtotal), 0);
  // El descuento se aplica una sola vez sobre el total y no línea por línea,
  // porque así lo va a aplicar el cupón de Tienda Nube sobre el carrito. Con
  // dos redondeos distintos, el total de la app y el del checkout se separan.
  const total = conDescuento(subtotal, descuento);
  const ahorro = subtotal - total;
  const hayComprables = lineas.some((l) => !l.discontinuado);

  const volver = () => {
    if (router.canGoBack()) router.back();
    else router.replace('/tienda');
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
      <View style={styles.header}>
        <Pressable onPress={volver} hitSlop={12} style={styles.icono} accessibilityRole="button">
          <Feather name="x" size={20} color={colors.ink} />
        </Pressable>
        <AppText variant="section">Tu carrito</AppText>
        {items.length > 0 ? (
          <Pressable onPress={vaciar} hitSlop={12} style={styles.vaciar} accessibilityRole="button">
            <AppText variant="meta">Vaciar</AppText>
          </Pressable>
        ) : (
          <View style={styles.icono} />
        )}
      </View>

      {items.length === 0 ? (
        <Vacio />
      ) : (
        <>
          <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
            {lineas.map((linea) => (
              <Fila
                key={linea.productoId}
                linea={linea}
                descuento={descuento}
                onCambiar={(cantidad) => cambiarCantidad(linea.productoId, cantidad)}
                onQuitar={() => quitar(linea.productoId)}
              />
            ))}
          </ScrollView>

          <View style={styles.pie}>
            {descuento > 0 && hayComprables ? (
              <>
                <View style={styles.totalRow}>
                  <AppText variant="meta">Subtotal</AppText>
                  <AppText variant="meta">{formatPrecio(subtotal)}</AppText>
                </View>
                <View style={styles.totalRow}>
                  <AppText variant="meta">
                    Descuento de la app ({formatPorcentaje(descuento)})
                  </AppText>
                  <AppText variant="meta">−{formatPrecio(ahorro)}</AppText>
                </View>
              </>
            ) : null}

            <View style={styles.totalRow}>
              <AppText variant="cardTitle">Total</AppText>
              <AppText variant="cardTitle">{formatPrecio(total)}</AppText>
            </View>
            {/*
              Deshabilitado hasta que exista el checkout: la emisión del cupón y
              el WebView de Tienda Nube dependen del alta como partner
              (COMPRA_EN_APP_SPEC.md §5.1 y §5.5).
            */}
            <Button label="Comprar" disabled />
            <AppText variant="meta" style={styles.aviso}>
              {hayComprables
                ? 'Estamos terminando la compra desde la app. Muy pronto vas a poder pagar tu pedido acá.'
                : 'Los productos de tu carrito ya no están disponibles.'}
            </AppText>
          </View>
        </>
      )}
    </SafeAreaView>
  );
}

function Fila({
  linea,
  descuento,
  onCambiar,
  onQuitar,
}: {
  linea: Linea;
  descuento: number;
  onCambiar: (cantidad: number) => void;
  onQuitar: () => void;
}) {
  const foto = resolveMediaUrl(linea.foto);

  return (
    <View style={[styles.fila, linea.discontinuado && styles.filaApagada]}>
      <Pressable
        style={styles.miniatura}
        onPress={() => router.push(`/producto/${linea.productoId}`)}
        accessibilityRole="button"
        accessibilityLabel={linea.nombre}>
        {foto ? (
          <Image source={{ uri: foto }} style={styles.img} contentFit="contain" transition={150} />
        ) : (
          <Feather name="droplet" size={18} color={colors.taupe} />
        )}
      </Pressable>

      <View style={styles.datos}>
        {linea.marca ? (
          <AppText variant="meta" numberOfLines={1}>
            {linea.marca}
          </AppText>
        ) : null}
        <AppText variant="cardTitle" numberOfLines={2} style={styles.nombre}>
          {linea.nombre}
        </AppText>

        {linea.discontinuado ? (
          <AppText variant="meta" color={colors.danger}>
            Ya no está disponible
          </AppText>
        ) : (
          <AppText variant="meta">
            {formatPrecio(conDescuento(linea.unitario, descuento))} c/u
          </AppText>
        )}

        <View style={styles.controles}>
          {linea.discontinuado ? (
            <Pressable onPress={onQuitar} hitSlop={8} accessibilityRole="button">
              <AppText variant="meta" color={colors.ink}>
                Quitar
              </AppText>
            </Pressable>
          ) : (
            <Stepper
              cantidad={linea.cantidad}
              onCambiar={onCambiar}
              onQuitar={onQuitar}
              nombre={linea.nombre}
            />
          )}
          {linea.discontinuado ? null : (
            <AppText variant="price">
              {formatPrecio(conDescuento(linea.subtotal, descuento))}
            </AppText>
          )}
        </View>
      </View>
    </View>
  );
}

function Stepper({
  cantidad,
  onCambiar,
  onQuitar,
  nombre,
}: {
  cantidad: number;
  onCambiar: (cantidad: number) => void;
  onQuitar: () => void;
  nombre: string;
}) {
  // En 1, el "−" saca el producto: es lo que espera cualquiera que apriete de
  // menos, y ahorra tener que buscar un tachito aparte.
  const menos = () => (cantidad <= 1 ? onQuitar() : onCambiar(cantidad - 1));
  const tope = cantidad >= MAX_POR_PRODUCTO;

  return (
    <View style={styles.stepper}>
      <Pressable
        onPress={menos}
        hitSlop={8}
        style={styles.paso}
        accessibilityRole="button"
        accessibilityLabel={cantidad <= 1 ? `Quitar ${nombre}` : `Restar una unidad de ${nombre}`}>
        <Feather name={cantidad <= 1 ? 'trash-2' : 'minus'} size={14} color={colors.ink} />
      </Pressable>

      <AppText variant="price" style={styles.cantidad}>
        {cantidad}
      </AppText>

      <Pressable
        onPress={() => onCambiar(cantidad + 1)}
        disabled={tope}
        hitSlop={8}
        style={[styles.paso, tope && styles.pasoApagado]}
        accessibilityRole="button"
        accessibilityState={{ disabled: tope }}
        accessibilityLabel={`Sumar una unidad de ${nombre}`}>
        <Feather name="plus" size={14} color={colors.ink} />
      </Pressable>
    </View>
  );
}

function Vacio() {
  return (
    <View style={styles.vacio}>
      <Feather name="shopping-bag" size={24} color={colors.taupe} />
      <AppText variant="cardTitle">Tu carrito está vacío</AppText>
      <AppText variant="meta" style={styles.vacioTxt}>
        Cuando encuentres algo que te guste, agregalo desde su ficha.
      </AppText>
      <Pressable
        onPress={() => router.replace('/tienda')}
        hitSlop={8}
        style={styles.verTienda}
        accessibilityRole="button">
        <AppText variant="meta" color={colors.ink}>
          Ver la tienda
        </AppText>
      </Pressable>
    </View>
  );
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
  vaciar: { width: 40, height: 40, justifyContent: 'center', alignItems: 'flex-end' },

  content: { paddingHorizontal: spacing.xl, paddingBottom: spacing.xl, gap: spacing.md },

  fila: {
    flexDirection: 'row',
    gap: spacing.md,
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    padding: spacing.md,
  },
  filaApagada: { opacity: 0.6 },
  miniatura: {
    width: 66,
    height: 66,
    borderRadius: radius.sm,
    backgroundColor: colors.cream,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  img: { width: '100%', height: '100%' },
  datos: { flex: 1, gap: 2 },
  nombre: { fontSize: 15, lineHeight: 18 },
  controles: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: spacing.sm,
  },

  stepper: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.pill,
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
  },
  paso: { width: 26, height: 26, alignItems: 'center', justifyContent: 'center' },
  pasoApagado: { opacity: 0.35 },
  cantidad: { minWidth: 16, textAlign: 'center' },

  pie: {
    gap: spacing.sm,
    paddingHorizontal: spacing.xl,
    paddingTop: spacing.lg,
    paddingBottom: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.line,
    backgroundColor: colors.ivory,
  },
  totalRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  aviso: { textAlign: 'center', lineHeight: 16 },

  vacio: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    padding: spacing.xl,
  },
  vacioTxt: { textAlign: 'center', lineHeight: 17 },
  verTienda: {
    marginTop: spacing.md,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.lg,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
  },
});
