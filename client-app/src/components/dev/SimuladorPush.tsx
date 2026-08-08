/**
 * Panel de simulación de notificaciones. Solo se ve en desarrollo.
 *
 * Dispara notificaciones locales con la misma carga útil que manda el backend,
 * así se puede probar el banner, el tap, el deep link y el refresco de datos sin
 * cuenta de Expo ni teléfono real.
 *
 * Donde no hay notificaciones nativas --web, o Expo Go en Android-- el panel
 * explica por qué en vez de desaparecer: si no, parecería que el simulador está
 * roto.
 */
import { useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

import { AppText } from '@/components/ui/AppText';
import { Card } from '@/components/ui/Card';
import {
  MOTIVO_NO_DISPONIBLE,
  NOTIFICACIONES_DISPONIBLES,
  notificaciones,
} from '@/services/notificacionesNativas';
import { AVISOS_DE_MUESTRA, DEMORA_SEGUNDOS, simularAviso } from '@/services/pushSimulador';
import { colors, radius, spacing } from '@/theme/ame';

export function SimuladorPush() {
  const [aviso, setAviso] = useState<string | null>(null);

  if (!__DEV__) return null;

  if (!NOTIFICACIONES_DISPONIBLES) {
    return (
      <View style={styles.seccion}>
        <AppText variant="label" style={styles.label}>
          Simulador de avisos (solo dev)
        </AppText>
        <Card>
          <AppText variant="meta">{MOTIVO_NO_DISPONIBLE}</AppText>
        </Card>
      </View>
    );
  }

  async function disparar(muestra: (typeof AVISOS_DE_MUESTRA)[number]) {
    const N = notificaciones();
    if (!N) return;

    // Las notificaciones locales también piden permiso en iOS y en Android 13+.
    const { status } = await N.getPermissionsAsync();
    if (status !== 'granted') {
      const pedido = await N.requestPermissionsAsync();
      if (pedido.status !== 'granted') {
        setAviso('Sin permiso de notificaciones: no se puede simular.');
        return;
      }
    }

    await simularAviso(muestra);
    setAviso(
      `"${muestra.etiqueta}" llega en ${DEMORA_SEGUNDOS} s. ` +
        'Mandá la app al fondo para verla como la ve la clienta.',
    );
  }

  return (
    <View style={styles.seccion}>
      <AppText variant="label" style={styles.label}>
        Simulador de avisos (solo dev)
      </AppText>

      <Card padded={false}>
        {AVISOS_DE_MUESTRA.map((muestra, i) => (
          <Pressable
            key={muestra.clave}
            onPress={() => disparar(muestra)}
            accessibilityRole="button"
            style={({ pressed }) => [
              styles.fila,
              i > 0 && styles.filaBorde,
              pressed && styles.presionada,
            ]}>
            <View style={styles.texto}>
              <AppText variant="cardTitle">{muestra.etiqueta}</AppText>
              <AppText variant="meta">
                {muestra.categoria} · → {muestra.ruta}
              </AppText>
            </View>
          </Pressable>
        ))}
      </Card>

      {aviso ? (
        <AppText variant="meta" style={styles.resultado}>
          {aviso}
        </AppText>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  seccion: { gap: spacing.md },
  label: { marginLeft: 2 },
  fila: { paddingHorizontal: spacing.lg, paddingVertical: spacing.lg },
  filaBorde: { borderTopWidth: 1, borderTopColor: colors.line },
  presionada: { backgroundColor: colors.blush, borderRadius: radius.sm },
  texto: { gap: 2 },
  resultado: { marginLeft: 2 },
});
