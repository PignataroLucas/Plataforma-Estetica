import { router } from 'expo-router';
import { Pressable, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { AppText } from '@/components/ui/AppText';
import { Button } from '@/components/ui/Button';
import { colors, fonts, spacing } from '@/theme/ame';

export default function Bienvenida() {
  return (
    <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
      <View style={styles.hero}>
        <AppText variant="label" style={styles.kicker}>
          Bienvenida a
        </AppText>
        <AppText style={styles.wordmark}>AME</AppText>
        <AppText style={styles.sub}>esencial</AppText>
        <AppText variant="body" color={colors.muted} style={styles.pitch}>
          Tu ritual de cuidado, tus turnos y tus beneficios, en un solo lugar.
        </AppText>
      </View>

      <View style={styles.actions}>
        <Button label="Ingresar con mi código" onPress={() => router.push('/codigo')} />
        <Button
          label="Crear una cuenta"
          variant="ghost"
          onPress={() => router.push('/registro')}
        />
        <Pressable
          onPress={() => router.push('/login')}
          hitSlop={8}
          style={styles.loginLink}
          accessibilityRole="button">
          <AppText variant="meta">¿Ya tenés cuenta? </AppText>
          <AppText variant="meta" color={colors.ink} style={styles.loginStrong}>
            Iniciar sesión
          </AppText>
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.ivory,
    paddingHorizontal: spacing.xl,
    paddingBottom: spacing.xl,
  },
  hero: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  kicker: { marginBottom: spacing.md },
  wordmark: {
    fontFamily: fonts.serifRegular,
    fontSize: 76,
    letterSpacing: 8,
    color: colors.ink,
    lineHeight: 82,
  },
  sub: {
    fontFamily: fonts.serifRegular,
    fontSize: 22,
    letterSpacing: 6,
    color: colors.muted,
    marginTop: -2,
  },
  pitch: {
    textAlign: 'center',
    lineHeight: 21,
    marginTop: spacing.xl,
    paddingHorizontal: spacing.md,
  },
  actions: { gap: spacing.md },
  loginLink: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: spacing.sm,
    paddingVertical: spacing.sm,
  },
  loginStrong: { textDecorationLine: 'underline' },
});
