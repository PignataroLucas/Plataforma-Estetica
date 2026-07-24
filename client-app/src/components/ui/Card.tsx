import { View, ViewProps, StyleSheet } from 'react-native';

import { colors, radius, spacing } from '@/theme/ame';

interface CardProps extends ViewProps {
  padded?: boolean;
}

export function Card({ padded = true, style, ...rest }: CardProps) {
  return <View {...rest} style={[styles.card, padded && styles.padded, style]} />;
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.card,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
  },
  padded: { padding: spacing.lg },
});
