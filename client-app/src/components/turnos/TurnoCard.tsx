import { Feather } from '@expo/vector-icons';
import { useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, View } from 'react-native';

import { EstadoBadge } from '@/components/turnos/EstadoBadge';
import { AppText } from '@/components/ui/AppText';
import { colors, radius, spacing } from '@/theme/ame';
import type { TurnoApp } from '@/types/api';
import { formatFechaLarga, formatHora, formatPrecio } from '@/utils/format';

interface Props {
  turno: TurnoApp;
  /** El próximo turno se destaca con la card oscura de la marca. */
  destacado?: boolean;
  onCancelar?: (turno: TurnoApp) => void;
  cancelando?: boolean;
}

/** Paleta de la card según si va sobre fondo oscuro o claro. */
function tonos(destacado: boolean) {
  if (destacado) {
    return {
      fondo: '#171310',
      borde: 'transparent',
      titulo: colors.onDark,
      texto: colors.onDark,
      meta: colors.onDarkMuted,
      linea: 'rgba(239,231,220,0.12)',
      icono: colors.onDarkMuted,
    };
  }
  return {
    fondo: colors.card,
    borde: colors.line,
    titulo: colors.ink,
    texto: colors.ink,
    meta: colors.muted,
    linea: colors.line,
    icono: colors.muted,
  };
}

export function TurnoCard({ turno, destacado = false, onCancelar, cancelando = false }: Props) {
  const [confirmando, setConfirmando] = useState(false);
  const t = tonos(destacado);

  const detalles = [
    { icon: 'clock' as const, texto: `${formatHora(turno.fecha_hora_inicio)} · ${turno.duracion_minutos} min` },
    turno.profesional_nombre
      ? { icon: 'user' as const, texto: turno.profesional_nombre }
      : null,
    { icon: 'map-pin' as const, texto: turno.sucursal_nombre },
  ].filter((d): d is { icon: 'clock' | 'user' | 'map-pin'; texto: string } => d !== null);

  return (
    <View style={[styles.card, { backgroundColor: t.fondo, borderColor: t.borde }]}>
      <View style={styles.head}>
        <EstadoBadge estado={turno.estado} onDark={destacado} />
        <AppText variant="price" color={t.texto}>
          {formatPrecio(turno.monto_total)}
        </AppText>
      </View>

      <AppText variant="cardTitle" color={t.titulo} style={styles.servicio}>
        {turno.servicio_nombre}
      </AppText>
      <AppText variant="body" color={t.texto}>
        {formatFechaLarga(turno.fecha_hora_inicio)}
      </AppText>

      <View style={styles.detalles}>
        {detalles.map((d) => (
          <View key={d.icon} style={styles.detalle}>
            <Feather name={d.icon} size={13} color={t.icono} />
            <AppText variant="meta" color={t.meta}>
              {d.texto}
            </AppText>
          </View>
        ))}
      </View>

      {onCancelar && turno.puede_cancelar ? (
        <View style={[styles.acciones, { borderTopColor: t.linea }]}>
          {confirmando ? (
            <View style={styles.confirmar}>
              <AppText variant="meta" color={t.meta} style={styles.pregunta}>
                ¿Cancelar este turno? No se puede deshacer.
              </AppText>
              <View style={styles.confirmarBotones}>
                <Pressable
                  onPress={() => setConfirmando(false)}
                  disabled={cancelando}
                  hitSlop={8}
                  style={styles.accion}>
                  <AppText variant="meta" color={t.texto}>
                    No, volver
                  </AppText>
                </Pressable>
                <Pressable
                  onPress={() => onCancelar(turno)}
                  disabled={cancelando}
                  hitSlop={8}
                  style={styles.accion}>
                  {cancelando ? (
                    <ActivityIndicator size="small" color={colors.danger} />
                  ) : (
                    <AppText variant="meta" color={colors.danger}>
                      Sí, cancelar
                    </AppText>
                  )}
                </Pressable>
              </View>
            </View>
          ) : (
            <Pressable onPress={() => setConfirmando(true)} hitSlop={8} style={styles.accion}>
              <AppText variant="meta" color={t.meta}>
                Cancelar turno
              </AppText>
            </Pressable>
          )}
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: radius.lg,
    borderWidth: 1,
    padding: 17,
  },
  head: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.md,
  },
  servicio: { lineHeight: 21, marginBottom: 3 },
  detalles: { gap: 5, marginTop: spacing.md },
  detalle: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  acciones: { marginTop: 14, paddingTop: 12, borderTopWidth: 1 },
  accion: { paddingVertical: 2 },
  confirmar: { gap: spacing.sm },
  pregunta: { lineHeight: 16 },
  confirmarBotones: { flexDirection: 'row', gap: spacing.xl },
});
