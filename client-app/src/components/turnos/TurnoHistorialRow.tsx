import { StyleSheet, View } from 'react-native';

import { EstadoBadge } from '@/components/turnos/EstadoBadge';
import { AppText } from '@/components/ui/AppText';
import { colors, spacing } from '@/theme/ame';
import type { TurnoApp } from '@/types/api';
import { formatFechaCorta, formatHora } from '@/utils/format';

/** Fila compacta del historial de turnos. */
export function TurnoHistorialRow({ turno }: { turno: TurnoApp }) {
  return (
    <View style={styles.row}>
      <View style={styles.info}>
        <AppText variant="body" numberOfLines={1}>
          {turno.servicio_nombre}
        </AppText>
        <AppText variant="meta">
          {formatFechaCorta(turno.fecha_hora_inicio)} · {formatHora(turno.fecha_hora_inicio)}
        </AppText>
      </View>
      <EstadoBadge estado={turno.estado} />
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: spacing.md,
    paddingVertical: 13,
    borderBottomWidth: 1,
    borderBottomColor: colors.line,
  },
  info: { flex: 1, minWidth: 0, gap: 3 },
});
