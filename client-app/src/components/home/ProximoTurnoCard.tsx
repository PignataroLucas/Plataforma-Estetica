import { View, StyleSheet } from 'react-native';

import { AppText } from '@/components/ui/AppText';
import { colors, fonts, radius, spacing } from '@/theme/ame';

interface Props {
  servicio: string;
  fecha: string;
  profesional?: string;
  iniciales?: string;
}

export function ProximoTurnoCard({ servicio, fecha, profesional, iniciales }: Props) {
  return (
    <View style={styles.card}>
      <AppText variant="label" color={colors.onDarkMuted}>
        Próximo turno
      </AppText>
      <AppText variant="cardTitle" color={colors.onDark} style={styles.servicio}>
        {servicio}
      </AppText>
      <AppText variant="meta" color={colors.onDarkMuted}>
        {fecha}
      </AppText>

      {profesional ? (
        <View style={styles.proRow}>
          <View style={styles.proAvatar}>
            <AppText style={styles.proInitials}>{iniciales ?? profesional.charAt(0)}</AppText>
          </View>
          <AppText variant="meta" color={colors.onDark}>
            {profesional}
          </AppText>
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#171310',
    borderRadius: radius.lg,
    padding: 17,
    overflow: 'hidden',
  },
  servicio: { marginTop: 9, marginBottom: 5, lineHeight: 21 },
  proRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginTop: 13,
    paddingTop: 13,
    borderTopWidth: 1,
    borderTopColor: 'rgba(239,231,220,0.12)',
  },
  proAvatar: {
    width: 23,
    height: 23,
    borderRadius: radius.pill,
    backgroundColor: 'rgba(232,209,205,0.22)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  proInitials: { fontFamily: fonts.sansMedium, fontSize: 9, color: colors.onDark, letterSpacing: 0.4 },
});
