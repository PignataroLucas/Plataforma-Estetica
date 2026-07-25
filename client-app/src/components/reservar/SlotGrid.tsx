import { Pressable, StyleSheet, View } from 'react-native';

import { AppText } from '@/components/ui/AppText';
import { colors, radius, spacing } from '@/theme/ame';
import type { SlotDisponible } from '@/types/api';

interface Props {
  slots: SlotDisponible[];
  /** ISO del slot elegido. */
  seleccionado: string | null;
  onSeleccionar: (slot: SlotDisponible) => void;
}

/** Grilla de horarios libres. */
export function SlotGrid({ slots, seleccionado, onSeleccionar }: Props) {
  return (
    <View style={styles.grid}>
      {slots.map((slot) => {
        const activo = slot.inicio === seleccionado;
        return (
          <Pressable
            key={slot.inicio}
            onPress={() => onSeleccionar(slot)}
            accessibilityRole="button"
            accessibilityState={{ selected: activo }}
            style={({ pressed }) => [
              styles.chip,
              activo && styles.chipActivo,
              pressed && !activo && styles.chipPresionado,
            ]}>
            <AppText variant="body" color={activo ? colors.onDark : colors.ink}>
              {slot.hora}
            </AppText>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  chip: {
    minWidth: 74,
    alignItems: 'center',
    paddingVertical: 11,
    paddingHorizontal: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.card,
  },
  chipActivo: { backgroundColor: colors.ink, borderColor: colors.ink },
  chipPresionado: { backgroundColor: colors.cream },
});
