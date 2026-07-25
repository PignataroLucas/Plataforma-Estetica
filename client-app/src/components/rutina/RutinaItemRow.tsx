import { Feather } from '@expo/vector-icons';
import { StyleSheet, View } from 'react-native';

import { AppText } from '@/components/ui/AppText';
import { colors, spacing } from '@/theme/ame';
import type { RutinaItem } from '@/types/api';

import { ProductoMini } from './ProductoMini';

/** Un paso de la rutina: título + nota, y el producto (card o texto) si lo hay. */
export function RutinaItemRow({ item, index }: { item: RutinaItem; index: number }) {
  const titulo = item.paso || item.producto?.nombre || item.producto_texto || 'Paso';
  // Mostramos el texto libre del producto solo si no pisa al título ni hay card.
  const mostrarProductoTexto = !item.producto && !!item.producto_texto && !!item.paso;

  return (
    <View style={styles.item}>
      <View style={styles.head}>
        <View style={styles.badge}>
          <AppText variant="meta" color={colors.muted} style={styles.badgeTxt}>
            {index}
          </AppText>
        </View>
        <View style={styles.headText}>
          <AppText variant="cardTitle" style={styles.paso}>
            {titulo}
          </AppText>
          {item.nota ? <AppText variant="meta">{item.nota}</AppText> : null}
        </View>
      </View>

      {item.producto ? (
        <View style={styles.producto}>
          <ProductoMini producto={item.producto} />
        </View>
      ) : mostrarProductoTexto ? (
        <View style={styles.prodTexto}>
          <Feather name="tag" size={12} color={colors.muted} />
          <AppText variant="meta">{item.producto_texto}</AppText>
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  item: { gap: spacing.sm },
  head: { flexDirection: 'row', gap: spacing.md, alignItems: 'flex-start' },
  badge: {
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 1,
    borderColor: colors.line,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 1,
  },
  badgeTxt: { fontSize: 10 },
  headText: { flex: 1, minWidth: 0, gap: 1 },
  paso: { fontSize: 16, lineHeight: 19 },
  producto: { marginLeft: 34 },
  prodTexto: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginLeft: 34,
  },
});
