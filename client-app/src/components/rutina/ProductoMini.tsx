import { Feather } from '@expo/vector-icons';
import { Image } from 'expo-image';
import { router } from 'expo-router';
import { Pressable, StyleSheet, View } from 'react-native';

import { AppText } from '@/components/ui/AppText';
import { resolveMediaUrl } from '@/services/config';
import { colors, radius, spacing } from '@/theme/ame';
import type { ProductoPublico } from '@/types/api';
import { formatPrecio } from '@/utils/format';

/** Card compacta de un producto del catálogo dentro de la rutina. */
export function ProductoMini({ producto }: { producto: ProductoPublico }) {
  // La miniatura alcanza para 44px; el original queda para la ficha.
  const foto = resolveMediaUrl(producto.foto_thumb ?? producto.foto);
  const abrirFicha = () => router.push(`/producto/${producto.id}`);

  return (
    <Pressable
      style={styles.card}
      onPress={abrirFicha}
      accessibilityRole="button"
      accessibilityLabel={`Ver ${producto.nombre}`}>
      <View style={styles.thumb}>
        {foto ? (
          <Image source={{ uri: foto }} style={styles.img} contentFit="cover" transition={150} />
        ) : (
          <Feather name="droplet" size={15} color={colors.muted} />
        )}
      </View>

      <View style={styles.info}>
        <AppText variant="cardTitle" numberOfLines={1} style={styles.nombre}>
          {producto.nombre}
        </AppText>
        {producto.marca ? (
          <AppText variant="meta" numberOfLines={1}>
            {producto.marca}
          </AppText>
        ) : null}
        <View style={styles.precioRow}>
          <AppText variant="price">{formatPrecio(producto.precio)}</AppText>
          {producto.en_oferta && producto.porcentaje_descuento > 0 ? (
            <View style={styles.oferta}>
              <AppText variant="label" color={colors.ink} style={styles.ofertaTxt}>
                -{producto.porcentaje_descuento}%
              </AppText>
            </View>
          ) : null}
        </View>
      </View>

      {/*
        Sigue sin haber checkout. Hasta que se decida por dónde se compra, el
        botón abre la ficha: está encima de la card, así que un onPress vacío lo
        convertiría en una zona muerta que además tapa el toque de la card.
      */}
      <Pressable
        style={({ pressed }) => [styles.comprar, pressed && styles.comprarPressed]}
        onPress={abrirFicha}
        accessibilityRole="button"
        accessibilityLabel={`Ver ${producto.nombre}`}>
        <AppText variant="button" color={colors.onDark} style={styles.comprarTxt}>
          Comprar
        </AppText>
      </Pressable>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    padding: spacing.sm,
  },
  thumb: {
    width: 44,
    height: 44,
    borderRadius: radius.sm,
    backgroundColor: colors.cream,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  img: { width: '100%', height: '100%' },
  info: { flex: 1, minWidth: 0, gap: 1 },
  nombre: { fontSize: 16, lineHeight: 18 },
  precioRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginTop: 2 },
  oferta: {
    backgroundColor: colors.blush,
    borderRadius: radius.sm,
    paddingHorizontal: 6,
    paddingVertical: 1,
  },
  ofertaTxt: { color: colors.ink },
  comprar: {
    backgroundColor: colors.ink,
    borderRadius: radius.sm,
    paddingHorizontal: spacing.md,
    paddingVertical: 8,
  },
  comprarPressed: { opacity: 0.85 },
  comprarTxt: { fontSize: 12 },
});
