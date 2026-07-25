import { Feather } from '@expo/vector-icons';
import { ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { AppText } from '@/components/ui/AppText';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { useAuthStore } from '@/stores/auth';
import { colors, fonts, radius, spacing } from '@/theme/ame';

export default function Perfil() {
  const usuario = useAuthStore((s) => s.usuario);
  const logout = useAuthStore((s) => s.logout);

  const nombreCompleto =
    [usuario?.nombre, usuario?.apellido].filter(Boolean).join(' ') || 'Tu cuenta';
  const inicial = (usuario?.nombre || usuario?.email || '?').trim().charAt(0).toUpperCase();
  const vinculaciones = usuario?.vinculaciones ?? [];

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <View style={styles.avatar}>
            <AppText style={styles.avatarTxt}>{inicial}</AppText>
          </View>
          <AppText variant="title" style={styles.name}>
            {nombreCompleto}
          </AppText>
          {usuario?.email ? <AppText variant="meta">{usuario.email}</AppText> : null}
        </View>

        {vinculaciones.length > 0 ? (
          <View style={styles.section}>
            <AppText variant="label" style={styles.sectionLabel}>
              Mis centros
            </AppText>
            <Card padded={false}>
              {vinculaciones.map((v, i) => (
                <View key={v.id} style={[styles.row, i > 0 && styles.rowBorder]}>
                  <Feather name="map-pin" size={16} color={colors.muted} />
                  <View style={styles.rowText}>
                    <AppText variant="cardTitle">{v.centro_nombre}</AppText>
                    <AppText variant="meta">{v.cliente_nombre}</AppText>
                  </View>
                </View>
              ))}
            </Card>
          </View>
        ) : null}

        <View style={styles.section}>
          <Button label="Cerrar sesión" variant="ghost" onPress={() => logout()} />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.ivory },
  content: {
    paddingHorizontal: spacing.xl,
    paddingTop: spacing.xxl,
    paddingBottom: spacing.xxl,
    gap: spacing.xl,
  },
  header: { alignItems: 'center', gap: 6 },
  avatar: {
    width: 76,
    height: 76,
    borderRadius: radius.pill,
    backgroundColor: colors.blush,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.sm,
  },
  avatarTxt: { fontFamily: fonts.serif, fontSize: 32, color: '#8a6f68' },
  name: { textAlign: 'center' },
  section: { gap: spacing.md },
  sectionLabel: { marginLeft: 2 },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.lg,
  },
  rowBorder: { borderTopWidth: 1, borderTopColor: colors.line },
  rowText: { gap: 2 },
});
