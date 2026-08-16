import { Feather } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';
import { Image } from 'expo-image';
import { router, useLocalSearchParams } from 'expo-router';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { BotonCarrito } from '@/components/carrito/BotonCarrito';
import { AppText } from '@/components/ui/AppText';
import { Button } from '@/components/ui/Button';
import { useCentroActivo } from '@/hooks/useCentroActivo';
import { useDescuentoApp } from '@/hooks/useDescuentoApp';
import { resolveMediaUrl } from '@/services/config';
import { getProducto } from '@/services/public';
import { MAX_POR_PRODUCTO, useCantidadDeProducto, useCarritoStore } from '@/stores/carrito';
import { colors, radius, spacing } from '@/theme/ame';
import type { ProductoPublico } from '@/types/api';
import { formatPrecio, parsearBeneficios } from '@/utils/format';
import { conDescuento, formatPorcentaje } from '@/utils/precios';

/**
 * Ficha de un producto: lo que el centro carga en el CRM (foto, descripción,
 * marca, precio). Es pantalla de stack, no tab — se llega desde la Tienda o
 * desde un paso de Mi rutina.
 */
export default function FichaProductoScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const productoId = Number(id);
  const { centroId } = useCentroActivo();

  const { data, isPending, isError, refetch } = useQuery({
    queryKey: ['producto', productoId, centroId],
    queryFn: () => getProducto(productoId, centroId),
    enabled: Number.isFinite(productoId),
  });

  const volver = () => {
    if (router.canGoBack()) router.back();
    else router.replace('/tienda');
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
      <View style={styles.header}>
        <Pressable onPress={volver} hitSlop={12} style={styles.back} accessibilityRole="button">
          <Feather name="chevron-left" size={22} color={colors.ink} />
        </Pressable>
        <AppText variant="section">Producto</AppText>
        <View style={styles.back}>
          <BotonCarrito />
        </View>
      </View>

      {isPending ? (
        <View style={styles.center}>
          <ActivityIndicator color={colors.muted} />
        </View>
      ) : isError || !data ? (
        <View style={styles.center}>
          <AppText variant="body" color={colors.muted} style={styles.centerTxt}>
            No pudimos cargar este producto.
          </AppText>
          <Pressable onPress={() => refetch()} hitSlop={8} style={styles.retry}>
            <AppText variant="meta" color={colors.ink}>
              Reintentar
            </AppText>
          </Pressable>
        </View>
      ) : (
        <Ficha producto={data} />
      )}
    </SafeAreaView>
  );
}

function Ficha({ producto }: { producto: ProductoPublico }) {
  const { porcentaje: descuento } = useDescuentoApp();
  // Acá sí el original: es la foto grande y es la única pantalla que la baja.
  const foto = resolveMediaUrl(producto.foto ?? producto.foto_thumb);
  const enOferta = producto.en_oferta && producto.porcentaje_descuento > 0;
  const descripcion = producto.descripcion.trim();
  const beneficios = parsearBeneficios(producto.beneficios);
  const sinContenido = !descripcion && beneficios.length === 0;

  return (
    <>
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}>
        <View style={styles.hero}>
          {foto ? (
            <Image
              source={{ uri: foto }}
              style={styles.img}
              contentFit="contain"
              transition={200}
              accessibilityLabel={producto.nombre}
            />
          ) : (
            <Feather name="droplet" size={32} color={colors.taupe} />
          )}
        </View>

        <View style={styles.titulo}>
          {producto.marca ? <AppText variant="meta">{producto.marca}</AppText> : null}
          <AppText variant="section">{producto.nombre}</AppText>

          <View style={styles.precioRow}>
            <AppText variant="price" style={styles.precio}>
              {formatPrecio(conDescuento(producto.precio, descuento))}
            </AppText>
            {descuento > 0 ? (
              <AppText variant="meta" style={styles.precioLista}>
                {formatPrecio(producto.precio)}
              </AppText>
            ) : null}
            {enOferta ? (
              <View style={styles.oferta}>
                <AppText variant="label" color={colors.ink}>
                  -{producto.porcentaje_descuento}% OFF
                </AppText>
              </View>
            ) : null}
          </View>

          {/*
            Se dice de dónde sale el precio, y no por transparencia nada más: el
            descuento es el incentivo para instalar la app (§1), así que tiene
            que verse que existe.
          */}
          {descuento > 0 ? (
            <AppText variant="meta">
              Precio con tu {formatPorcentaje(descuento)} de descuento de la app
            </AppText>
          ) : null}
        </View>

        {descripcion ? (
          <Seccion titulo="Qué es">
            <AppText variant="body" style={styles.parrafo}>
              {descripcion}
            </AppText>
          </Seccion>
        ) : null}

        {beneficios.length > 0 ? (
          <Seccion titulo="Beneficios">
            <View style={styles.beneficios}>
              {beneficios.map((b) => (
                <View key={b} style={styles.beneficio}>
                  <View style={styles.bullet} />
                  <AppText variant="body" style={styles.beneficioTxt}>
                    {b}
                  </AppText>
                </View>
              ))}
            </View>
          </Seccion>
        ) : null}

        {producto.contenido_ml ? (
          <Seccion titulo="Contenido">
            <AppText variant="body">{producto.contenido_ml} ml</AppText>
          </Seccion>
        ) : null}

        {/*
          Sin contenido la ficha es una foto y un precio. Vale más decirlo que
          dejar la pantalla en blanco: lo carga el centro y esto avisa que falta,
          en vez de parecer un error de la app.
        */}
        {sinContenido ? (
          <View style={styles.sinContenido}>
            <AppText variant="meta" style={styles.sinContenidoTxt}>
              Todavía no cargamos el detalle de este producto. Consultanos y te
              contamos todo.
            </AppText>
          </View>
        ) : null}
      </ScrollView>

      {/*
        Un producto sin variante de Tienda Nube no se puede comprar: la URL del
        carrito se arma con ese id (§5.2). El botón no se muestra en vez de
        fallar al tocarlo.
      */}
      {producto.comprable ? <PieDeCompra producto={producto} /> : null}
    </>
  );
}

/**
 * Pie fijo de la ficha: agregar al carrito.
 *
 * Fijo y no al final del scroll porque la ficha puede ser larga (descripción y
 * beneficios los carga el centro) y la acción no puede depender de que la
 * clienta llegue hasta abajo.
 */
function PieDeCompra({ producto }: { producto: ProductoPublico }) {
  const { centroId } = useCentroActivo();
  const agregar = useCarritoStore((s) => s.agregar);
  const cantidad = useCantidadDeProducto(producto.id);
  const tope = cantidad >= MAX_POR_PRODUCTO;

  return (
    <View style={styles.pie}>
      {cantidad > 0 ? (
        <Pressable
          onPress={() => router.push('/carrito')}
          hitSlop={8}
          style={styles.enCarrito}
          accessibilityRole="button">
          <AppText variant="meta">
            {cantidad === 1 ? 'Ya tenés 1 en el carrito' : `Ya tenés ${cantidad} en el carrito`}
          </AppText>
          <AppText variant="meta" color={colors.ink}>
            Ver carrito
          </AppText>
        </Pressable>
      ) : null}

      <Button
        label={cantidad > 0 ? 'Agregar otra' : 'Agregar al carrito'}
        disabled={tope}
        onPress={() => agregar(producto, centroId)}
      />

      {tope ? (
        <AppText variant="meta" style={styles.topeTxt}>
          Es el máximo por producto. Si necesitás más, escribinos.
        </AppText>
      ) : null}
    </View>
  );
}

function Seccion({ titulo, children }: { titulo: string; children: React.ReactNode }) {
  return (
    <View style={styles.seccion}>
      <AppText variant="cardTitle">{titulo}</AppText>
      {children}
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
  back: { width: 40, height: 40, justifyContent: 'center' },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.md,
    padding: spacing.xl,
  },
  centerTxt: { textAlign: 'center' },
  retry: {
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.lg,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
  },
  scroll: { flex: 1 },
  content: { paddingHorizontal: spacing.xl, paddingBottom: spacing.xxl, gap: spacing.lg },

  pie: {
    gap: spacing.sm,
    paddingHorizontal: spacing.xl,
    paddingTop: spacing.md,
    paddingBottom: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: colors.line,
    backgroundColor: colors.ivory,
  },
  enCarrito: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  topeTxt: { textAlign: 'center' },

  hero: {
    aspectRatio: 1,
    backgroundColor: colors.cream,
    borderRadius: radius.lg,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  img: { width: '100%', height: '100%' },

  titulo: { gap: spacing.xs },
  precioRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, marginTop: spacing.xs },
  precio: { fontSize: 20 },
  precioLista: { textDecorationLine: 'line-through' },
  oferta: {
    backgroundColor: colors.blush,
    borderRadius: radius.sm,
    paddingHorizontal: 8,
    paddingVertical: 2,
  },

  seccion: { gap: spacing.sm },
  parrafo: { lineHeight: 21 },

  beneficios: { gap: spacing.sm },
  beneficio: { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.md },
  bullet: {
    width: 5,
    height: 5,
    borderRadius: radius.pill,
    backgroundColor: colors.taupe,
    marginTop: 8,
  },
  beneficioTxt: { flex: 1, lineHeight: 21 },

  sinContenido: {
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    padding: spacing.lg,
  },
  sinContenidoTxt: { lineHeight: 18 },
});
