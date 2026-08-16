import { Feather } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';
import { Image } from 'expo-image';
import { router } from 'expo-router';
import { useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  useWindowDimensions,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { BotonCarrito } from '@/components/carrito/BotonCarrito';
import { AppText } from '@/components/ui/AppText';
import { SearchBar } from '@/components/ui/SearchBar';
import { useCentroActivo } from '@/hooks/useCentroActivo';
import { useDescuentoApp } from '@/hooks/useDescuentoApp';
import { resolveMediaUrl } from '@/services/config';
import { getProductos } from '@/services/public';
import { colors, radius, spacing } from '@/theme/ame';
import type { ProductoPublico } from '@/types/api';
import { formatPrecio } from '@/utils/format';
import { conDescuento } from '@/utils/precios';

const TODAS = '__todas__';
const COLUMNAS = 2;

/**
 * Catálogo de productos.
 *
 * Es una tab propia y no una sección de Promos: un catálogo y un programa de
 * beneficios no son lo mismo, y mezclarlos hace que ninguno de los dos se
 * entienda.
 */
export default function TiendaScreen() {
  const { centroId } = useCentroActivo();
  const { porcentaje: descuento } = useDescuentoApp();
  const [busqueda, setBusqueda] = useState('');
  const [filtro, setFiltro] = useState<string>(TODAS);

  const { data, isPending, isError, refetch } = useQuery({
    queryKey: ['productos', centroId],
    queryFn: () => getProductos(centroId),
  });

  const productos = useMemo(() => data?.results ?? [], [data]);

  /**
   * Las categorías salen de los productos, no de un endpoint aparte. Hoy
   * ninguno tiene categoría cargada, así que los chips no se muestran; el día
   * que el centro empiece a categorizar aparecen solos, sin tocar nada.
   */
  const categorias = useMemo(() => {
    const nombres = productos
      .map((p) => p.categoria_nombre)
      .filter((n): n is string => Boolean(n));
    return Array.from(new Set(nombres)).sort((a, b) => a.localeCompare(b, 'es'));
  }, [productos]);

  const visibles = useMemo(() => {
    const texto = busqueda.trim().toLowerCase();
    return productos.filter((p) => {
      const porCategoria = filtro === TODAS || p.categoria_nombre === filtro;
      const porTexto =
        !texto ||
        p.nombre.toLowerCase().includes(texto) ||
        p.marca.toLowerCase().includes(texto);
      return porCategoria && porTexto;
    });
  }, [productos, filtro, busqueda]);

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.header}>
        <AppText variant="section">Tienda</AppText>
        <BotonCarrito />
      </View>

      {isPending ? (
        <View style={styles.center}>
          <ActivityIndicator color={colors.muted} />
        </View>
      ) : isError ? (
        <View style={styles.center}>
          <AppText variant="body" color={colors.muted} style={styles.centerTxt}>
            No pudimos cargar los productos.
          </AppText>
          <Pressable onPress={() => refetch()} hitSlop={8} style={styles.retry}>
            <AppText variant="meta" color={colors.ink}>
              Reintentar
            </AppText>
          </Pressable>
        </View>
      ) : (
        <ScrollView
          contentContainerStyle={styles.content}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled">
          <SearchBar value={busqueda} onChangeText={setBusqueda} />

          {categorias.length > 0 ? (
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.chips}>
              <Chip label="Todos" activo={filtro === TODAS} onPress={() => setFiltro(TODAS)} />
              {categorias.map((c) => (
                <Chip key={c} label={c} activo={filtro === c} onPress={() => setFiltro(c)} />
              ))}
            </ScrollView>
          ) : null}

          {visibles.length === 0 ? (
            <Vacio conFiltro={busqueda.trim() !== '' || filtro !== TODAS} />
          ) : (
            <View style={styles.grilla}>
              {visibles.map((p) => (
                <ProductoCard key={p.id} producto={p} descuento={descuento} />
              ))}
            </View>
          )}
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

function ProductoCard({
  producto,
  descuento,
}: {
  producto: ProductoPublico;
  descuento: number;
}) {
  const { width } = useWindowDimensions();
  // Dos columnas: el ancho útil menos los márgenes laterales y el hueco del medio.
  const ancho = (width - spacing.xl * 2 - spacing.md) / COLUMNAS;

  // La grilla usa la miniatura; el original queda para la ficha. Si el producto
  // se cargó antes de que existieran las miniaturas, cae al original.
  const foto = resolveMediaUrl(producto.foto_thumb ?? producto.foto);
  const enOferta = producto.en_oferta && producto.porcentaje_descuento > 0;

  return (
    <Pressable
      style={[styles.card, { width: ancho }]}
      onPress={() => router.push(`/producto/${producto.id}`)}
      accessibilityRole="button"
      accessibilityLabel={producto.nombre}>
      <View style={styles.imagen}>
        {foto ? (
          <Image
            source={{ uri: foto }}
            style={styles.img}
            // `contain` y no `cover`: las fotos de producto que saca el centro
            // son verticales y de proporciones irregulares, y recortar corta
            // etiquetas y tapas. Prefiere aire alrededor antes que cortar.
            contentFit="contain"
            transition={150}
            accessibilityLabel={producto.nombre}
          />
        ) : (
          <Feather name="droplet" size={22} color={colors.taupe} />
        )}

        {enOferta ? (
          <View style={styles.oferta}>
            <AppText variant="label" color={colors.ink}>
              -{producto.porcentaje_descuento}%
            </AppText>
          </View>
        ) : null}
      </View>

      <View style={styles.info}>
        {producto.marca ? (
          <AppText variant="meta" numberOfLines={1}>
            {producto.marca}
          </AppText>
        ) : null}
        <AppText variant="cardTitle" numberOfLines={2} style={styles.nombre}>
          {producto.nombre}
        </AppText>
        {descuento > 0 ? (
          <View style={styles.precios}>
            <AppText variant="price">
              {formatPrecio(conDescuento(producto.precio, descuento))}
            </AppText>
            <AppText variant="meta" style={styles.precioLista}>
              {formatPrecio(producto.precio)}
            </AppText>
          </View>
        ) : (
          <AppText variant="price">{formatPrecio(producto.precio)}</AppText>
        )}
      </View>
    </Pressable>
  );
}

function Chip({ label, activo, onPress }: { label: string; activo: boolean; onPress: () => void }) {
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityState={{ selected: activo }}
      style={[styles.chip, activo && styles.chipActivo]}>
      <AppText variant="meta" color={activo ? colors.onDark : colors.ink}>
        {label}
      </AppText>
    </Pressable>
  );
}

function Vacio({ conFiltro }: { conFiltro: boolean }) {
  return (
    <View style={styles.vacio}>
      <Feather name="shopping-bag" size={24} color={colors.taupe} />
      <AppText variant="cardTitle" style={styles.vacioTitulo}>
        {conFiltro ? 'Sin resultados' : 'Todavía no hay productos'}
      </AppText>
      <AppText variant="meta" style={styles.vacioTxt}>
        {conFiltro
          ? 'Probá con otra búsqueda.'
          : 'Cuando el centro cargue su catálogo, lo vas a ver acá.'}
      </AppText>
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
    // Alto fijo: el botón del carrito aparece y desaparece según haya items, y
    // sin esto el título salta cuando se agrega el primero.
    minHeight: 52,
  },
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
  content: { paddingHorizontal: spacing.xl, paddingBottom: spacing.xxl, gap: spacing.lg },

  chips: { gap: spacing.sm, paddingRight: spacing.xl },
  chip: {
    paddingVertical: 7,
    paddingHorizontal: 14,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.card,
  },
  chipActivo: { backgroundColor: colors.ink, borderColor: colors.ink },

  grilla: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md },
  card: {
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    overflow: 'hidden',
  },
  imagen: {
    // Proporción fija para toda la grilla: sin esto, cada foto le da otra
    // altura a su tarjeta y las filas quedan desparejas.
    aspectRatio: 1,
    backgroundColor: colors.cream,
    alignItems: 'center',
    justifyContent: 'center',
  },
  img: { width: '100%', height: '100%' },
  oferta: {
    position: 'absolute',
    top: spacing.sm,
    left: spacing.sm,
    backgroundColor: colors.blush,
    borderRadius: radius.sm,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  info: { padding: spacing.md, gap: 2 },
  precios: { flexDirection: 'row', alignItems: 'baseline', gap: spacing.sm },
  precioLista: { textDecorationLine: 'line-through' },
  nombre: { fontSize: 15, lineHeight: 18 },

  vacio: { alignItems: 'center', gap: spacing.sm, paddingVertical: spacing.xxl },
  vacioTitulo: { marginTop: spacing.sm },
  vacioTxt: { textAlign: 'center', lineHeight: 17 },
});
