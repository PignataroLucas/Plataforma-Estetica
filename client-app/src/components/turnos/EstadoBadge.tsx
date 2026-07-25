import { StyleSheet, View } from 'react-native';

import { AppText } from '@/components/ui/AppText';
import { colors, radius, spacing } from '@/theme/ame';
import type { EstadoTurno } from '@/types/api';

/**
 * Etiqueta de estado del turno. Usa textos propios de la app (los del backend
 * están escritos para el staff, ej: "Pendiente de Confirmación").
 */
const ESTADOS: Record<EstadoTurno, { label: string; punto: string }> = {
  PENDIENTE: { label: 'A confirmar', punto: colors.taupe },
  CONFIRMADO: { label: 'Confirmado', punto: colors.ink },
  COMPLETADO: { label: 'Realizado', punto: colors.muted },
  CANCELADO: { label: 'Cancelado', punto: colors.danger },
  NO_SHOW: { label: 'No asististe', punto: colors.danger },
};

interface Props {
  estado: EstadoTurno;
  /** Sobre la card oscura del próximo turno. */
  onDark?: boolean;
}

export function EstadoBadge({ estado, onDark = false }: Props) {
  const cfg = ESTADOS[estado] ?? { label: estado, punto: colors.muted };
  // El punto casi negro se pierde sobre la card oscura.
  const punto = onDark && cfg.punto === colors.ink ? colors.onDark : cfg.punto;

  return (
    <View style={[styles.badge, onDark ? styles.badgeDark : styles.badgeClaro]}>
      <View style={[styles.punto, { backgroundColor: punto }]} />
      <AppText variant="meta" color={onDark ? colors.onDark : colors.ink}>
        {cfg.label}
      </AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    alignSelf: 'flex-start',
    borderRadius: radius.pill,
    borderWidth: 1,
    paddingVertical: 3,
    paddingHorizontal: spacing.sm,
  },
  badgeClaro: { borderColor: colors.line, backgroundColor: colors.ivory },
  badgeDark: { borderColor: 'rgba(239,231,220,0.18)', backgroundColor: 'rgba(239,231,220,0.06)' },
  punto: { width: 6, height: 6, borderRadius: radius.pill },
});
