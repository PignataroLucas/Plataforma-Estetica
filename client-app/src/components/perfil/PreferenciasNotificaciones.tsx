/**
 * Qué avisos quiere recibir la clienta.
 *
 * Las categorías espejan las del backend (`apps/notificaciones/eventos.py`), que
 * son también los canales de Android: alguien puede silenciar Promociones desde
 * los ajustes del sistema o desde acá, y son dos cosas distintas --esto le dice
 * al backend que no mande; el canal solo decide cómo suena lo que ya llegó.
 *
 * El interruptor se mueve antes de que conteste el servidor, a propósito: con la
 * red de un celular, un switch que tarda medio segundo en moverse se siente
 * roto y la clienta lo toca de nuevo. Si el PATCH falla, vuelve solo y se avisa.
 *
 * Lo de "igual te avisamos" no es letra chica de relleno: confirmar y cancelar
 * un turno están marcados como transaccionales en el backend y se mandan aunque
 * la categoría esté apagada. Sin ese renglón, apagar Turnos promete un silencio
 * que no existe, y el próximo aviso parece un bug.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { ActivityIndicator, StyleSheet, Switch, View } from 'react-native';

import { AppText } from '@/components/ui/AppText';
import { Card } from '@/components/ui/Card';
import {
  actualizarPreferencias,
  CATEGORIAS,
  getPreferencias,
  type Categoria,
  type Preferencias,
} from '@/services/push';
import { colors, spacing } from '@/theme/ame';

const CLAVE = ['preferencias-notificaciones'] as const;

const TEXTOS: Record<Categoria, { titulo: string; detalle: string }> = {
  TURNOS: { titulo: 'Turnos', detalle: 'Recordatorios antes de cada turno.' },
  RUTINA: { titulo: 'Mi rutina', detalle: 'Cuando actualizamos tu rutina, y sus recordatorios.' },
  NOVEDADES: { titulo: 'Novedades', detalle: 'Tu cumpleaños y fechas nuevas para reservar.' },
  PROMOCIONES: { titulo: 'Promociones', detalle: 'Ofertas y promos del centro.' },
};

export function PreferenciasNotificaciones() {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  const { data, isPending, isError } = useQuery({
    queryKey: CLAVE,
    queryFn: getPreferencias,
  });

  const { mutate } = useMutation({
    mutationFn: actualizarPreferencias,
    onMutate: async (cambios: Partial<Preferencias>) => {
      // Sin esto, un refetch en vuelo puede pisar el cambio optimista.
      await queryClient.cancelQueries({ queryKey: CLAVE });
      const previas = queryClient.getQueryData<Preferencias>(CLAVE);
      if (previas) queryClient.setQueryData<Preferencias>(CLAVE, { ...previas, ...cambios });
      return { previas };
    },
    onError: (_error, _cambios, contexto) => {
      if (contexto?.previas) queryClient.setQueryData(CLAVE, contexto.previas);
      setError('No pudimos guardar el cambio. Probá de nuevo.');
    },
    onSuccess: (delServidor) => {
      // La respuesta trae el set completo: se usa esa y no la optimista.
      queryClient.setQueryData(CLAVE, delServidor);
      setError(null);
    },
  });

  return (
    <View style={styles.seccion}>
      <AppText variant="label" style={styles.label}>
        Avisos
      </AppText>

      {isPending ? (
        <Card style={styles.centrada}>
          <ActivityIndicator color={colors.muted} />
        </Card>
      ) : isError || !data ? (
        <Card>
          <AppText variant="meta">No pudimos cargar tus preferencias.</AppText>
        </Card>
      ) : (
        <>
          <Card padded={false}>
            {CATEGORIAS.map((categoria, i) => (
              <View key={categoria} style={[styles.fila, i > 0 && styles.filaBorde]}>
                <View style={styles.texto}>
                  <AppText variant="cardTitle">{TEXTOS[categoria].titulo}</AppText>
                  <AppText variant="meta">{TEXTOS[categoria].detalle}</AppText>
                </View>
                <Switch
                  value={data[categoria]}
                  onValueChange={(valor) => mutate({ [categoria]: valor })}
                  trackColor={{ false: colors.taupe, true: colors.ink }}
                  thumbColor={colors.card}
                  ios_backgroundColor={colors.taupe}
                  accessibilityLabel={TEXTOS[categoria].titulo}
                />
              </View>
            ))}
          </Card>

          <AppText variant="meta" style={styles.nota}>
            Si te confirmamos o cancelamos un turno te avisamos igual, aunque tengas Turnos
            apagado.
          </AppText>

          {error ? (
            <AppText variant="meta" color={colors.danger}>
              {error}
            </AppText>
          ) : null}
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  seccion: { gap: spacing.md },
  label: { marginLeft: 2 },
  centrada: { alignItems: 'center' },
  fila: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: spacing.md,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
  },
  filaBorde: { borderTopWidth: 1, borderTopColor: colors.line },
  texto: { flex: 1, gap: 2 },
  nota: { marginLeft: 2, lineHeight: 15 },
});
