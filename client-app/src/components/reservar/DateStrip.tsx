import { Pressable, ScrollView, StyleSheet, View } from 'react-native';

import { AppText } from '@/components/ui/AppText';
import { colors, fonts, radius, spacing } from '@/theme/ame';
import { etiquetasDeDia, fechaISOLocal } from '@/utils/format';

interface Props {
  /** Días a mostrar, empezando por hoy. */
  dias: Date[];
  /** Fecha elegida en formato YYYY-MM-DD. */
  seleccionada: string;
  onSeleccionar: (fecha: string) => void;
}

/** Selector horizontal de días para elegir la fecha del turno. */
export function DateStrip({ dias, seleccionada, onSeleccionar }: Props) {
  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={styles.strip}>
      {dias.map((dia) => {
        const iso = fechaISOLocal(dia);
        const activo = iso === seleccionada;
        const { diaSemana, numero, mes } = etiquetasDeDia(dia);

        return (
          <Pressable
            key={iso}
            onPress={() => onSeleccionar(iso)}
            accessibilityRole="button"
            accessibilityState={{ selected: activo }}
            style={({ pressed }) => [
              styles.dia,
              activo && styles.diaActivo,
              pressed && !activo && styles.diaPresionado,
            ]}>
            <AppText variant="label" color={activo ? colors.onDarkMuted : colors.muted}>
              {diaSemana}
            </AppText>
            <AppText style={[styles.numero, activo && styles.numeroActivo]}>{numero}</AppText>
            <AppText variant="meta" color={activo ? colors.onDarkMuted : colors.muted}>
              {mes}
            </AppText>
          </Pressable>
        );
      })}
      <View style={styles.colita} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  strip: { gap: spacing.sm, paddingVertical: 2 },
  dia: {
    width: 58,
    alignItems: 'center',
    gap: 2,
    paddingVertical: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.card,
  },
  diaActivo: { backgroundColor: colors.ink, borderColor: colors.ink },
  diaPresionado: { backgroundColor: colors.cream },
  numero: { fontFamily: fonts.serif, fontSize: 20, color: colors.ink, lineHeight: 24 },
  numeroActivo: { color: colors.onDark },
  // Aire al final para que el último día no quede pegado al borde.
  colita: { width: spacing.md },
});
