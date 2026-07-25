import { forwardRef, useState } from 'react';
import { StyleSheet, TextInput, TextInputProps, View } from 'react-native';

import { colors, fonts, radius, spacing } from '@/theme/ame';

import { AppText } from './AppText';

interface FieldProps extends TextInputProps {
  label?: string;
  /** Mensaje de error bajo el campo (resalta el borde). */
  error?: string | null;
}

/** Input de texto con etiqueta y estado de error, según el sistema AME. */
export const Field = forwardRef<TextInput, FieldProps>(function Field(
  { label, error, style, onFocus, onBlur, ...rest },
  ref,
) {
  const [focused, setFocused] = useState(false);

  const handleFocus: NonNullable<TextInputProps['onFocus']> = (e) => {
    setFocused(true);
    onFocus?.(e);
  };
  const handleBlur: NonNullable<TextInputProps['onBlur']> = (e) => {
    setFocused(false);
    onBlur?.(e);
  };

  return (
    <View style={styles.wrap}>
      {label ? (
        <AppText variant="label" style={styles.label}>
          {label}
        </AppText>
      ) : null}
      <TextInput
        ref={ref}
        placeholderTextColor={colors.muted}
        selectionColor={colors.ink}
        style={[
          styles.input,
          focused && styles.inputFocused,
          !!error && styles.inputError,
          style,
        ]}
        onFocus={handleFocus}
        onBlur={handleBlur}
        {...rest}
      />
      {error ? (
        <AppText variant="meta" color={colors.danger} style={styles.error}>
          {error}
        </AppText>
      ) : null}
    </View>
  );
});

const styles = StyleSheet.create({
  wrap: { gap: 7 },
  label: { marginLeft: 2 },
  input: {
    fontFamily: fonts.sans,
    fontSize: 14,
    color: colors.ink,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    paddingHorizontal: 15,
    paddingVertical: 13,
  },
  inputFocused: { borderColor: colors.focus },
  inputError: { borderColor: colors.danger },
  error: { marginLeft: 2, color: colors.danger },
});
