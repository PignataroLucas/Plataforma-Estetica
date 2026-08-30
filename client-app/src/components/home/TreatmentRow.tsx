import { Feather } from '@expo/vector-icons';
import { View, StyleSheet } from 'react-native';

import { AppText } from '@/components/ui/AppText';
import { Presionable } from '@/components/ui/Presionable';
import { colors, radius, spacing } from '@/theme/ame';

type FeatherName = keyof typeof Feather.glyphMap;

interface Props {
  nombre: string;
  meta: string;
  precio: string;
  icon?: FeatherName;
  /** Con `onPress` la fila abre la ficha del tratamiento. */
  onPress?: () => void;
}

export function TreatmentRow({ nombre, meta, precio, icon = 'droplet', onPress }: Props) {
  const contenido = (
    <>
      <View style={styles.pic}>
        <Feather name={icon} size={16} color={colors.ink} />
      </View>
      <View style={styles.info}>
        <AppText variant="cardTitle" style={styles.nombre}>
          {nombre}
        </AppText>
        <AppText variant="meta" numberOfLines={1}>
          {meta}
        </AppText>
      </View>
      <AppText variant="price">{precio}</AppText>
      {onPress ? <Feather name="chevron-right" size={16} color={colors.muted} /> : null}
    </>
  );

  if (!onPress) return <View style={styles.row}>{contenido}</View>;

  return (
    <Presionable
      onPress={onPress}
      accessibilityRole="button"
      style={styles.row}>
      {contenido}
    </Presionable>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    paddingVertical: 11,
    paddingHorizontal: spacing.md,
  },
  pic: {
    width: 36,
    height: 36,
    borderRadius: radius.pill,
    backgroundColor: colors.cream,
    alignItems: 'center',
    justifyContent: 'center',
  },
  info: { flex: 1, minWidth: 0 },
  nombre: { fontSize: 16, lineHeight: 18 },
});
