import { ActivityIndicator, StyleSheet, View } from 'react-native';

import { colors, radius, spacing } from '@/theme/ame';

import { AppText } from './AppText';
import { Presionable, type PresionableProps } from './Presionable';

interface ButtonProps extends Omit<PresionableProps, 'children'> {
  label: string;
  variant?: 'primary' | 'ghost';
  loading?: boolean;
}

export function Button({
  label,
  variant = 'primary',
  loading = false,
  disabled,
  style,
  ...rest
}: ButtonProps) {
  const isGhost = variant === 'ghost';
  const isDisabled = disabled || loading;

  return (
    <Presionable
      accessibilityRole="button"
      accessibilityState={{ disabled: !!isDisabled, busy: loading }}
      disabled={isDisabled}
      style={[styles.base, isGhost ? styles.ghost : styles.primary, isDisabled && styles.disabled, style]}
      {...rest}>
      <View style={styles.inner}>
        {loading ? (
          <ActivityIndicator size="small" color={isGhost ? colors.ink : colors.onDark} />
        ) : (
          <AppText variant="button" color={isGhost ? colors.ink : colors.onDark}>
            {label}
          </AppText>
        )}
      </View>
    </Presionable>
  );
}

const styles = StyleSheet.create({
  base: {
    borderRadius: radius.md,
    paddingVertical: 14,
    paddingHorizontal: spacing.lg,
    alignItems: 'center',
    justifyContent: 'center',
  },
  inner: { minHeight: 18, justifyContent: 'center' },
  primary: { backgroundColor: colors.ink },
  ghost: { backgroundColor: 'transparent', borderWidth: 1, borderColor: colors.line },
  disabled: { opacity: 0.5 },
});
