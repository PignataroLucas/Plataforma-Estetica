import { Pressable, PressableProps, StyleSheet, View } from 'react-native';

import { colors, radius, spacing } from '@/theme/ame';

import { AppText } from './AppText';

interface ButtonProps extends Omit<PressableProps, 'children'> {
  label: string;
  variant?: 'primary' | 'ghost';
}

export function Button({ label, variant = 'primary', style, ...rest }: ButtonProps) {
  const isGhost = variant === 'ghost';
  return (
    <Pressable
      accessibilityRole="button"
      style={(state) => [
        styles.base,
        isGhost ? styles.ghost : styles.primary,
        // @ts-expect-error style can be a function result
        state.pressed && styles.pressed,
        typeof style === 'function' ? style(state) : style,
      ]}
      {...rest}>
      <View>
        <AppText variant="button" color={isGhost ? colors.ink : colors.onDark}>
          {label}
        </AppText>
      </View>
    </Pressable>
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
  primary: { backgroundColor: colors.ink },
  ghost: { backgroundColor: 'transparent', borderWidth: 1, borderColor: colors.line },
  pressed: { opacity: 0.85 },
});
