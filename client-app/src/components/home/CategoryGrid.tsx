import { Feather } from '@expo/vector-icons';
import { View, Pressable, StyleSheet } from 'react-native';

import { AppText } from '@/components/ui/AppText';
import { colors, radius, spacing } from '@/theme/ame';

type FeatherName = keyof typeof Feather.glyphMap;

interface Categoria {
  label: string;
  icon: FeatherName;
  bg: string;
}

const CATEGORIAS: Categoria[] = [
  { label: 'Facial', icon: 'user', bg: colors.blush },
  { label: 'Corporal', icon: 'droplet', bg: colors.cream },
  { label: 'Láser', icon: 'zap', bg: '#EFE7DC' },
  { label: 'Spa & relax', icon: 'star', bg: colors.taupe },
];

export function CategoryGrid() {
  return (
    <View style={styles.grid}>
      {CATEGORIAS.map((c) => (
        <Pressable key={c.label} style={[styles.cell, { backgroundColor: c.bg }]}>
          <Feather name={c.icon} size={22} color={colors.ink} />
          <AppText variant="body" style={styles.label}>
            {c.label}
          </AppText>
        </Pressable>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.md,
  },
  cell: {
    // dos por fila considerando el gap
    width: '47%',
    flexGrow: 1,
    borderRadius: radius.md,
    paddingVertical: 18,
    paddingHorizontal: 14,
    alignItems: 'center',
    gap: spacing.md,
  },
  label: { fontSize: 12 },
});
