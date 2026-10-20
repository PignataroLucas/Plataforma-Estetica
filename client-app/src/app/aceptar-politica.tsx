import { Feather } from '@expo/vector-icons';
import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { AppText } from '@/components/ui/AppText';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { ApiError } from '@/services/api';
import { abrirDocumento } from '@/services/legales';
import { useAuthStore } from '@/stores/auth';
import { colors, spacing } from '@/theme/ame';

/**
 * Aceptar la política de privacidad para seguir usando la app.
 *
 * La ven las cuentas creadas antes de que existiera la casilla del registro, y
 * todas cuando la política cambia de versión. Es la única pantalla accesible
 * hasta aceptar (ver el gate de `_layout.tsx`): no tiene vuelta atrás, solo
 * aceptar o cerrar sesión.
 */
export default function AceptarPolitica() {
  const pendientes = useAuthStore((s) => s.usuario?.legales_pendientes ?? []);
  const aceptarLegales = useAuthStore((s) => s.aceptarLegales);
  const logout = useAuthStore((s) => s.logout);

  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const aceptar = async () => {
    if (loading) return;
    setError(null);
    setLoading(true);
    try {
      await aceptarLegales();
      // Sin pendientes, el gate de navegación la lleva a la app solo.
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'No pudimos guardar tu respuesta.');
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.head}>
          <AppText variant="title">Tu privacidad</AppText>
          <AppText variant="body" color={colors.muted} style={styles.sub}>
            Para seguir usando la app, leé y aceptá la política de privacidad. Explica qué datos
            usamos, para qué, y cómo pedir que los borremos.
          </AppText>
        </View>

        <Card padded={false}>
          {pendientes.map((doc, i) => (
            <Pressable
              key={doc.documento}
              onPress={() => abrirDocumento(doc.ruta)}
              style={[styles.doc, i > 0 && styles.docBorde]}
              accessibilityRole="link">
              <Feather name="file-text" size={18} color={colors.muted} />
              <AppText variant="cardTitle" style={styles.docTitulo}>
                {doc.titulo}
              </AppText>
              <AppText variant="meta" color={colors.ink}>
                Leer
              </AppText>
            </Pressable>
          ))}
        </Card>

        {error ? (
          <AppText variant="meta" color={colors.danger}>
            {error}
          </AppText>
        ) : null}

        <View style={styles.acciones}>
          <Button label="Acepto" loading={loading} onPress={aceptar} />
          <Button
            label="Cerrar sesión"
            variant="ghost"
            disabled={loading}
            onPress={() => logout()}
          />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.ivory },
  content: {
    flexGrow: 1,
    paddingHorizontal: spacing.xl,
    paddingTop: spacing.xxl,
    paddingBottom: spacing.xxl,
    gap: spacing.xl,
  },
  head: { gap: spacing.sm },
  sub: { lineHeight: 20 },
  doc: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.lg,
  },
  docBorde: { borderTopWidth: 1, borderTopColor: colors.line },
  docTitulo: { flex: 1 },
  acciones: { gap: spacing.md },
});
