import { Feather } from '@expo/vector-icons';
import { router } from 'expo-router';
import { StyleSheet, View } from 'react-native';

import { SemanaRutina } from '@/components/rutina/SemanaRutina';
import { AppText } from '@/components/ui/AppText';
import { Presionable } from '@/components/ui/Presionable';
import { colors, fonts, radius, spacing } from '@/theme/ame';
import type { MomentoRutina, RutinaApp, RutinaHoy } from '@/types/api';
import { momentosDeHoy, resumenDelDia } from '@/utils/rutina';

const MOMENTO: Record<MomentoRutina, { nombre: string; icon: 'sun' | 'moon' }> = {
  DIURNA: { nombre: 'Mañana', icon: 'sun' },
  NOCTURNA: { nombre: 'Noche', icon: 'moon' },
};

/**
 * Card en Inicio con la rutina de hoy: qué falta, cómo va cada momento y la
 * semana. Lleva a "Mi rutina", que es donde se tilda.
 *
 * Sin `hoy` (rutinas viejas de texto libre, que no se pueden tildar) queda el
 * resumen de siempre.
 */
export function RutinaTeaser({ rutina, hoy }: { rutina: RutinaApp; hoy: RutinaHoy | null }) {
  const conCheckIn = hoy !== null && rutina.items.length > 0;

  return (
    <Presionable
      onPress={() => router.push('/mi-rutina')}
      style={styles.card}
      accessibilityRole="button">
      <View style={styles.top}>
        <View style={styles.icon}>
          <Feather name="feather" size={17} color={colors.ink} />
        </View>
        <View style={styles.info}>
          <AppText variant="label" color={conCheckIn ? colors.rose : undefined}>
            {conCheckIn ? 'Tu rutina de hoy' : 'Tu rutina'}
          </AppText>
          <AppText variant="cardTitle" style={styles.titulo}>
            {conCheckIn ? resumenDelDia(hoy) : 'Rutina de cuidado'}
          </AppText>
          {conCheckIn ? null : <AppText variant="meta">Ver los pasos de tu rutina</AppText>}
        </View>
        <Feather name="chevron-right" size={20} color={conCheckIn ? colors.rose : colors.muted} />
      </View>

      {conCheckIn ? (
        <>
          <View style={styles.pills}>
            {momentosDeHoy(hoy).map((m) => {
              const { hechos, total, cumplido } = hoy.momentos[m];
              const tinta = cumplido ? colors.onDark : colors.ink;
              return (
                <View key={m} style={[styles.pill, cumplido && styles.pillLista]}>
                  <Feather name={MOMENTO[m].icon} size={14} color={tinta} />
                  <AppText style={[styles.pillNombre, { color: tinta }]}>{MOMENTO[m].nombre}</AppText>
                  {cumplido ? <Feather name="check" size={13} color={tinta} /> : null}
                  <AppText style={[styles.pillCuenta, { color: cumplido ? tinta : colors.rose }]}>
                    {hechos}/{total}
                  </AppText>
                </View>
              );
            })}
          </View>

          <View style={styles.semana}>
            <SemanaRutina hoy={hoy} variante="puntos" />
            {hoy.racha > 0 ? (
              <View style={styles.racha}>
                <AppText style={styles.rachaNum}>{hoy.racha}</AppText>
                <AppText variant="meta" color={colors.rose}>
                  {hoy.racha === 1 ? 'día' : 'días seguidos'}
                </AppText>
              </View>
            ) : null}
          </View>
        </>
      ) : null}
    </Presionable>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: 14,
    backgroundColor: colors.blush,
    borderRadius: radius.md,
    padding: spacing.lg,
  },
  top: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  icon: {
    width: 40,
    height: 40,
    borderRadius: radius.pill,
    backgroundColor: 'rgba(255,255,255,0.55)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  info: { flex: 1, minWidth: 0, gap: 1 },
  titulo: { fontSize: 17 },
  pills: { flexDirection: 'row', gap: spacing.sm },
  pill: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 7,
    borderRadius: radius.pill,
    paddingVertical: 9,
    paddingHorizontal: spacing.md,
    backgroundColor: 'rgba(255,255,255,0.55)',
  },
  pillLista: { backgroundColor: colors.ink },
  pillNombre: { flex: 1, fontFamily: fonts.sans, fontSize: 12 },
  pillCuenta: { fontFamily: fonts.sansMedium, fontSize: 11 },
  semana: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderTopWidth: 1,
    borderTopColor: 'rgba(26,23,18,0.08)',
    paddingTop: spacing.md,
  },
  racha: { flexDirection: 'row', alignItems: 'baseline', gap: 5 },
  // lining-nums: con los números de estilo antiguo de Cormorant, el 1 se lee como una I.
  rachaNum: { fontFamily: fonts.serif, fontSize: 22, lineHeight: 24, color: colors.ink, fontVariant: ['lining-nums'] },
});
