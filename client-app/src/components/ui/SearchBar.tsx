import { Feather } from '@expo/vector-icons';
import { View, TextInput, StyleSheet } from 'react-native';

import { colors, fonts, radius, spacing } from '@/theme/ame';

interface SearchBarProps {
  placeholder?: string;
  /** Sin `value`/`onChangeText` el campo queda decorativo (así lo usa Inicio). */
  value?: string;
  onChangeText?: (texto: string) => void;
}

export function SearchBar({
  placeholder = 'Buscar tratamientos…',
  value,
  onChangeText,
}: SearchBarProps) {
  return (
    <View style={styles.wrap}>
      <Feather name="search" size={15} color={colors.muted} />
      <TextInput
        placeholder={placeholder}
        placeholderTextColor={colors.muted}
        style={styles.input}
        value={value}
        onChangeText={onChangeText}
        autoCorrect={false}
        returnKeyType="search"
        editable
      />
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    paddingHorizontal: 15,
    paddingVertical: 12,
  },
  input: {
    flex: 1,
    fontFamily: fonts.sansLight,
    fontSize: 12.5,
    color: colors.ink,
    padding: 0,
  },
});
