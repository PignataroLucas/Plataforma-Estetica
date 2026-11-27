import { Feather } from '@expo/vector-icons';
import { Pressable, StyleSheet, View } from 'react-native';

import { AppText } from '@/components/ui/AppText';
import { abrirDocumento } from '@/services/legales';
import { colors, spacing } from '@/theme/ame';

interface Props {
  value: boolean;
  onChange: (value: boolean) => void;
  error?: string | null;
}

/**
 * La casilla de la política de privacidad en los formularios de registro.
 *
 * Tocar el link abre la política y no tilda la casilla: aceptar tiene que ser un
 * gesto aparte de leer.
 */
export function AceptaPolitica({ value, onChange, error }: Props) {
  return (
    <View style={styles.wrap}>
      <Pressable
        onPress={() => onChange(!value)}
        hitSlop={8}
        style={styles.fila}
        accessibilityRole="checkbox"
        accessibilityState={{ checked: value }}>
        <Feather
          name={value ? 'check-square' : 'square'}
          size={20}
          color={error ? colors.danger : colors.ink}
        />
        <AppText variant="body" style={styles.texto}>
          Leí y acepto la{' '}
          <AppText
            variant="body"
            style={styles.link}
            onPress={() => abrirDocumento('/legales/privacidad/')}
            accessibilityRole="link">
            política de privacidad
          </AppText>
          .
        </AppText>
      </Pressable>
      {error ? (
        <AppText variant="meta" color={colors.danger}>
          {error}
        </AppText>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: spacing.xs },
  fila: { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.sm },
  texto: { flex: 1, lineHeight: 20 },
  link: { textDecorationLine: 'underline' },
});
