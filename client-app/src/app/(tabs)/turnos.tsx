import { Feather } from '@expo/vector-icons';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { router } from 'expo-router';
import { useMemo, useState } from 'react';
import { ActivityIndicator, Pressable, RefreshControl, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { TurnoCard } from '@/components/turnos/TurnoCard';
import { TurnoHistorialRow } from '@/components/turnos/TurnoHistorialRow';
import { AppText } from '@/components/ui/AppText';
import { Button } from '@/components/ui/Button';
import { useCentroActivo } from '@/hooks/useCentroActivo';
import { analytics } from '@/services/analytics';
import { ApiError } from '@/services/api';
import { cancelarTurno, getMisTurnos } from '@/services/turnos';
import { colors, radius, spacing } from '@/theme/ame';
import type { TurnoApp } from '@/types/api';
import { formatFechaCorta, formatHora } from '@/utils/format';

export default function TurnosScreen() {
  const { centroNombre } = useCentroActivo();
  const queryClient = useQueryClient();
  const [errorCancelar, setErrorCancelar] = useState<string | null>(null);

  const { data, isLoading, isError, refetch, isRefetching } = useQuery({
    queryKey: ['mis-turnos'],
    queryFn: () => getMisTurnos(),
  });

  const cancelacion = useMutation({
    mutationFn: (turno: TurnoApp) => cancelarTurno(turno.id),
    onSuccess: (_, turno) => {
      analytics.turnoCancelado(turno);
      setErrorCancelar(null);
      queryClient.invalidateQueries({ queryKey: ['mis-turnos'] });
    },
    onError: (error) => {
      setErrorCancelar(
        error instanceof ApiError ? error.message : 'No pudimos cancelar el turno.',
      );
    },
  });

  const proximos = data?.proximos ?? [];
  // Memoizado y no `?? []` suelto: el array vacío sería una referencia nueva en
  // cada render y los memos de abajo no servirían de nada.
  const todosLosHistoricos = useMemo(() => data?.historicos ?? [], [data]);

  /**
   * Los pedidos que el centro no pudo tomar y todavía tienen arreglo.
   *
   * El backend los manda en `historicos` porque un rechazado ya no ocupa agenda,
   * pero archivarlos ahí es justo lo contrario de lo que la clienta necesita:
   * el horario que pidió todavía no llegó y lo que quiere es elegir otro. Se
   * suben arriba con esa acción al lado y se sacan del historial, que es para
   * mirar, no para resolver.
   */
  const sinTomar = useMemo(
    () =>
      todosLosHistoricos.filter(
        (t) => t.estado === 'RECHAZADO' && new Date(t.fecha_hora_inicio) > new Date(),
      ),
    [todosLosHistoricos],
  );
  const historicos = useMemo(
    () => todosLosHistoricos.filter((t) => !sinTomar.includes(t)),
    [todosLosHistoricos, sinTomar],
  );

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.header}>
        {centroNombre ? <AppText variant="label">{centroNombre}</AppText> : null}
        <AppText variant="title" style={styles.titulo}>
          Turnos
        </AppText>
      </View>

      {isLoading ? (
        <View style={styles.center}>
          <ActivityIndicator color={colors.muted} />
        </View>
      ) : isError ? (
        <View style={styles.center}>
          <AppText variant="body" color={colors.muted} style={styles.centerText}>
            No pudimos cargar tus turnos.
          </AppText>
          <Pressable onPress={() => refetch()} hitSlop={8} style={styles.retry}>
            <AppText variant="meta" color={colors.ink}>
              Reintentar
            </AppText>
          </Pressable>
        </View>
      ) : (
        <ScrollView
          contentContainerStyle={styles.content}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={isRefetching}
              onRefresh={refetch}
              tintColor={colors.muted}
            />
          }>
          {errorCancelar ? (
            <View style={styles.banner}>
              <Feather name="alert-circle" size={14} color={colors.danger} />
              <AppText variant="meta" color={colors.danger} style={styles.bannerTxt}>
                {errorCancelar}
              </AppText>
            </View>
          ) : null}

          {sinTomar.map((turno) => (
            <SinPoderTomar key={turno.id} turno={turno} />
          ))}

          {proximos.length === 0 ? (
            <SinTurnos />
          ) : (
            <View style={styles.seccion}>
              <AppText variant="section">Próximos</AppText>
              <View style={styles.cards}>
                {proximos.map((turno, i) => (
                  <TurnoCard
                    key={turno.id}
                    turno={turno}
                    destacado={i === 0}
                    onCancelar={cancelacion.mutate}
                    cancelando={cancelacion.isPending && cancelacion.variables?.id === turno.id}
                  />
                ))}
              </View>
            </View>
          )}

          {historicos.length > 0 ? (
            <View style={styles.seccion}>
              <AppText variant="section">Historial</AppText>
              <View>
                {historicos.map((turno) => (
                  <TurnoHistorialRow key={turno.id} turno={turno} />
                ))}
              </View>
            </View>
          ) : null}
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

/**
 * Un pedido que el centro no pudo tomar, con el camino para volver a elegir.
 *
 * El texto no dice el motivo y es a propósito: el motivo queda en el CRM para
 * las métricas del centro. "No hay disponibilidad" es muy distinto de leer
 * "tiene una deuda", y la clienta no necesita el porqué para resolver — necesita
 * otro horario.
 */
function SinPoderTomar({ turno }: { turno: TurnoApp }) {
  return (
    <View style={styles.rechazado}>
      <View style={styles.rechazadoHead}>
        <Feather name="calendar" size={14} color={colors.muted} />
        <AppText variant="meta" style={styles.rechazadoTxt}>
          No pudimos tomar {turno.servicio_nombre} del{' '}
          {formatFechaCorta(turno.fecha_hora_inicio)} a las{' '}
          {formatHora(turno.fecha_hora_inicio)}.
        </AppText>
      </View>
      <Button
        label="Elegir otro horario"
        onPress={() => router.push('/reservar')}
        style={styles.rechazadoBoton}
      />
    </View>
  );
}

function SinTurnos() {
  return (
    <View style={styles.vacio}>
      <Feather name="calendar" size={26} color={colors.taupe} />
      <AppText variant="cardTitle" style={styles.vacioTitulo}>
        No tenés turnos reservados
      </AppText>
      <AppText variant="meta" style={styles.vacioTxt}>
        Reservá tu próximo tratamiento y lo vas a ver acá.
      </AppText>
      <Button
        label="Reservar un turno"
        onPress={() => router.push('/reservar')}
        style={styles.vacioBoton}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.ivory },
  rechazado: {
    gap: spacing.md,
    padding: spacing.lg,
    borderRadius: radius.md,
    backgroundColor: colors.cream,
  },
  rechazadoHead: { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.sm },
  rechazadoTxt: { flex: 1 },
  rechazadoBoton: { alignSelf: 'flex-start' },
  header: { paddingHorizontal: spacing.xl, paddingTop: spacing.sm, paddingBottom: 14 },
  titulo: { marginTop: 4 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: spacing.md, padding: spacing.xl },
  centerText: { textAlign: 'center' },
  retry: {
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.lg,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
  },
  content: { paddingHorizontal: spacing.xl, paddingBottom: spacing.xxl, gap: spacing.xxl },

  banner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: 'rgba(169,82,76,0.08)',
    borderRadius: radius.md,
    padding: spacing.md,
  },
  bannerTxt: { flex: 1, lineHeight: 16 },

  seccion: { gap: spacing.lg },
  cards: { gap: spacing.md },

  vacio: { alignItems: 'center', gap: spacing.sm, paddingVertical: spacing.xxl },
  vacioTitulo: { marginTop: spacing.sm },
  vacioTxt: { textAlign: 'center', lineHeight: 17 },
  vacioBoton: { alignSelf: 'stretch', marginTop: spacing.lg },
});
