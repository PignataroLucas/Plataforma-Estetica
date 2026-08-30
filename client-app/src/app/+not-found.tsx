/**
 * Ruta que no existe en esta versión de la app.
 *
 * No es decoración: la ruta a la que lleva cada notificación la manda el
 * backend (`apps/notificaciones/eventos.py`), y un teléfono con una versión
 * vieja instalada no conoce las rutas que se agregaron después. Sin esta
 * pantalla, ese tap cae en la pantalla de ruta no encontrada que trae
 * expo-router, que es de desarrollo y no se parece en nada a AME.
 *
 * `replace` y no `back`: si se llegó desde una notificación con la app cerrada,
 * no hay nada atrás a donde volver.
 */
import { router } from 'expo-router';
import { StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { AppText } from '@/components/ui/AppText';
import { Button } from '@/components/ui/Button';
import { colors, spacing } from '@/theme/ame';

export default function NoEncontrado() {
  return (
    <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
      <View style={styles.centro}>
        <AppText variant="section">No encontramos eso</AppText>
        <AppText variant="body" color={colors.muted} style={styles.texto}>
          Puede que el aviso sea viejo, o que esa sección todavía no esté en tu versión de la app.
        </AppText>
        <Button label="Ir al inicio" onPress={() => router.replace('/')} />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.ivory },
  centro: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.md,
    padding: spacing.xl,
  },
  texto: { textAlign: 'center', lineHeight: 20 },
});
