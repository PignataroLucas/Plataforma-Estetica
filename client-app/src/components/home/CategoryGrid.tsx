import { Feather } from '@expo/vector-icons';
import { router } from 'expo-router';
import { View, StyleSheet } from 'react-native';

import { AppText } from '@/components/ui/AppText';
import { Presionable } from '@/components/ui/Presionable';
import { colors, radius, spacing } from '@/theme/ame';

type FeatherName = keyof typeof Feather.glyphMap;

interface Props {
  /** Categorías reales del catálogo del centro. */
  categorias: string[];
}

/** Fondos que se van alternando: la grilla no depende de cuántas categorías haya. */
const FONDOS = [colors.blush, colors.cream, '#EFE7DC', colors.taupe];

/**
 * Ícono por palabra clave. Es cosmético: si el centro nombra sus categorías de
 * otra forma, cae en el ícono neutro y la grilla sigue funcionando igual.
 */
const ICONOS: { patron: RegExp; icon: FeatherName }[] = [
  { patron: /facial|rostro|piel/i, icon: 'user' },
  { patron: /corporal|cuerpo|reduc/i, icon: 'droplet' },
  { patron: /laser|láser|depilaci/i, icon: 'zap' },
  { patron: /spa|relax|masaje/i, icon: 'star' },
  { patron: /uñas|manos|pies|pedicur|manicur/i, icon: 'feather' },
];

function iconoDe(nombre: string): FeatherName {
  return ICONOS.find((i) => i.patron.test(nombre))?.icon ?? 'circle';
}

export function CategoryGrid({ categorias }: Props) {
  return (
    <View style={styles.grid}>
      {categorias.map((nombre, i) => (
        <Presionable
          key={nombre}
          accessibilityRole="button"
          onPress={() => router.push({ pathname: '/servicios', params: { categoria: nombre } })}
          style={[styles.cell, { backgroundColor: FONDOS[i % FONDOS.length] }]}>
          <Feather name={iconoDe(nombre)} size={22} color={colors.ink} />
          <AppText variant="body" style={styles.label} numberOfLines={1}>
            {nombre}
          </AppText>
        </Presionable>
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
