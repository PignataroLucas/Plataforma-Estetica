import { Feather } from '@expo/vector-icons';
import { Image } from 'expo-image';
import { Pressable, StyleSheet, View } from 'react-native';

import { AppText } from '@/components/ui/AppText';
import { resolveMediaUrl } from '@/services/config';
import { colors, radius, spacing } from '@/theme/ame';
import type { ProductoPublico } from '@/types/api';
import { formatPrecio } from '@/utils/format';

/** Card compacta de un producto del catálogo dentro de la rutina. */
export function ProductoMini({ producto }: { producto: ProductoPublico }) {
  const foto = resolveMediaUrl(producto.foto);

  return (
    <View style={styles.card}>
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

      {/* Stub de checkout (opción C): botón visible, sin acción todavía. */}
      <Pressable
        style={({ pressed }) => [styles.comprar, pressed && styles.comprarPressed]}
        onPress={() => {}}
        accessibilityRole="button"
        accessibilityLabel={`Comprar ${producto.nombre}`}>
        <AppText variant="button" color={colors.onDark} style={styles.comprarTxt}>
          Comprar
        </AppText>
      </Pressable>
    </View>
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
