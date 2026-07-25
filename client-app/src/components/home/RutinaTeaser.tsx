import { Feather } from '@expo/vector-icons';
import { router } from 'expo-router';
import { Pressable, StyleSheet, View } from 'react-native';

import { AppText } from '@/components/ui/AppText';
import { colors, radius, spacing } from '@/theme/ame';
import type { RutinaApp } from '@/types/api';

/** Card en Inicio que resume la rutina y lleva a la pantalla "Mi rutina". */
export function RutinaTeaser({ rutina }: { rutina: RutinaApp }) {
  const total = rutina.items.length;
  const resumen = total ? `Día y noche · ${total} pasos` : 'Ver los pasos de tu rutina';

  return (
    <Pressable
      onPress={() => router.push('/mi-rutina')}
      style={({ pressed }) => [styles.card, pressed && styles.pressed]}
      accessibilityRole="button">
      <View style={styles.icon}>
        <Feather name="feather" size={17} color={colors.ink} />
      </View>
      <View style={styles.info}>
        <AppText variant="label">Tu rutina</AppText>
        <AppText variant="cardTitle" style={styles.titulo}>
          Rutina de cuidado
        </AppText>
        <AppText variant="meta">{resumen}</AppText>
      </View>
      <Feather name="chevron-right" size={20} color={colors.muted} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    backgroundColor: colors.blush,
    borderRadius: radius.md,
    padding: spacing.lg,
  },
  pressed: { opacity: 0.9 },
  icon: {
    width: 40,
    height: 40,
    borderRadius: radius.pill,
    backgroundColor: 'rgba(255,255,255,0.55)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  info: { flex: 1, minWidth: 0, gap: 1 },
  titulo: { fontSize: 17 },
});
