import { Feather } from '@expo/vector-icons';
import { router } from 'expo-router';
import { ReactNode } from 'react';
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { AppText } from '@/components/ui/AppText';
import { colors, radius, spacing } from '@/theme/ame';

interface Props {
  title: string;
  subtitle?: string;
  /** Error general del formulario (credenciales, red, etc.). */
  error?: string | null;
  children: ReactNode;
  /** Zona inferior fija (links de navegación entre pantallas). */
  footer?: ReactNode;
}

/** Estructura común de las pantallas de autenticación: back, título y form. */
export function AuthScaffold({ title, subtitle, error, children, footer }: Props) {
  const volver = () => {
    if (router.canGoBack()) router.back();
    else router.replace('/bienvenida');
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView
          contentContainerStyle={styles.content}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}>
          <Pressable onPress={volver} hitSlop={12} style={styles.back} accessibilityRole="button">
            <Feather name="chevron-left" size={22} color={colors.ink} />
          </Pressable>

          <View style={styles.head}>
            <AppText variant="title">{title}</AppText>
            {subtitle ? (
              <AppText variant="body" color={colors.muted} style={styles.subtitle}>
                {subtitle}
              </AppText>
            ) : null}
          </View>

          {error ? (
            <View style={styles.banner}>
              <Feather name="alert-circle" size={15} color={colors.danger} />
              <AppText variant="meta" color={colors.danger} style={styles.bannerText}>
                {error}
              </AppText>
            </View>
          ) : null}

          <View style={styles.form}>{children}</View>

          {footer ? <View style={styles.footer}>{footer}</View> : null}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.ivory },
  flex: { flex: 1 },
  content: {
    flexGrow: 1,
    paddingHorizontal: spacing.xl,
    paddingTop: spacing.sm,
    paddingBottom: spacing.xxl,
  },
  back: { width: 40, height: 40, marginLeft: -8, justifyContent: 'center' },
  head: { marginTop: spacing.md, marginBottom: spacing.xl, gap: 6 },
  subtitle: { lineHeight: 20 },
  banner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: 'rgba(169,82,76,0.08)',
    borderRadius: radius.sm,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    marginBottom: spacing.lg,
  },
  bannerText: { flex: 1, lineHeight: 16 },
  form: { gap: spacing.lg },
  footer: { marginTop: spacing.xl, alignItems: 'center' },
});
