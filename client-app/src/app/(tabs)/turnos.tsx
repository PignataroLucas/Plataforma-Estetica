import { Feather } from '@expo/vector-icons';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { router } from 'expo-router';
import { useState } from 'react';
import { ActivityIndicator, Pressable, RefreshControl, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { TurnoCard } from '@/components/turnos/TurnoCard';
import { TurnoHistorialRow } from '@/components/turnos/TurnoHistorialRow';
import { AppText } from '@/components/ui/AppText';
import { Button } from '@/components/ui/Button';
import { useCentroActivo } from '@/hooks/useCentroActivo';
import { ApiError } from '@/services/api';
import { cancelarTurno, getMisTurnos } from '@/services/turnos';
import { colors, radius, spacing } from '@/theme/ame';
import type { TurnoApp } from '@/types/api';

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
    onSuccess: () => {
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
  const historicos = data?.historicos ?? [];

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
