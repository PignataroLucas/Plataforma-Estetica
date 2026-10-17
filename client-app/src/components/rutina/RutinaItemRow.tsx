import { Feather } from '@expo/vector-icons';
import { Pressable, StyleSheet, View } from 'react-native';

import { AppText } from '@/components/ui/AppText';
import { colors, fonts, radius, spacing } from '@/theme/ame';
import type { RutinaItem } from '@/types/api';
import { describirDias } from '@/utils/rutina';

import { ProductoMini } from './ProductoMini';

interface Props {
  item: RutinaItem;
  /** Si está, el paso se puede tildar: el círculo reemplaza al número. */
  onToggle?: () => void;
  hecho?: boolean;
  /** Número del paso, para los que no se tildan (los que hoy no van). */
  index?: number;
}

/** Un paso de la rutina: tilde (o número), título, nota, días y producto. */
export function RutinaItemRow({ item, onToggle, hecho = false, index }: Props) {
  const titulo = item.paso || item.producto?.nombre || item.producto_texto || 'Paso';
  // Mostramos el texto libre del producto solo si no pisa al título ni hay card.
  const mostrarProductoTexto = !item.producto && !!item.producto_texto && !!item.paso;
  const frecuencia = item.dias.length > 0
    ? `${describirDias(item.dias)}${item.va_hoy ? ' · hoy toca' : ''}`
    : null;

  return (
    <View style={styles.item}>
      <View style={styles.head}>
        {onToggle ? (
          <Pressable
            onPress={onToggle}
            hitSlop={10}
            style={styles.checkHit}
            accessibilityRole="checkbox"
            accessibilityState={{ checked: hecho }}
            accessibilityLabel={titulo}>
            <View style={[styles.check, hecho && styles.checkHecho]}>
              {hecho ? <Feather name="check" size={14} color={colors.onDark} /> : null}
            </View>
          </Pressable>
        ) : (
          <View style={styles.badge}>
            <AppText variant="meta" color={colors.muted} style={styles.badgeTxt}>
              {index ?? '·'}
            </AppText>
          </View>
        )}
        <View style={styles.headText}>
          {frecuencia ? (
            <View style={styles.frecuencia}>
              <Feather name="calendar" size={10} color={colors.rose} />
              <AppText style={styles.frecuenciaTxt}>{frecuencia}</AppText>
            </View>
          ) : null}
          <AppText variant="cardTitle" style={[styles.paso, hecho && styles.pasoHecho]}>
            {titulo}
          </AppText>
          {item.nota ? <AppText variant="meta">{item.nota}</AppText> : null}
        </View>
      </View>

      {item.producto ? (
        <View style={[styles.producto, hecho && styles.atenuado]}>
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
  checkHit: { marginTop: -1 },
  check: {
    width: 24,
    height: 24,
    borderRadius: radius.pill,
    borderWidth: 1.3,
    borderColor: 'rgba(26,23,18,0.3)',
    backgroundColor: colors.card,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkHecho: { backgroundColor: colors.ink, borderColor: colors.ink },
  badge: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.line,
    alignItems: 'center',
    justifyContent: 'center',
  },
  badgeTxt: { fontSize: 10 },
  headText: { flex: 1, minWidth: 0, gap: 1 },
  frecuencia: {
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: colors.blush,
    borderRadius: radius.pill,
    paddingHorizontal: 8,
    paddingVertical: 2,
    marginBottom: 3,
  },
  frecuenciaTxt: { fontFamily: fonts.sansMedium, fontSize: 9.5, letterSpacing: 0.3, color: colors.rose },
  paso: { fontSize: 16, lineHeight: 19 },
  pasoHecho: { color: colors.muted },
  producto: { marginLeft: 36 },
  atenuado: { opacity: 0.55 },
  prodTexto: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginLeft: 36,
  },
});
