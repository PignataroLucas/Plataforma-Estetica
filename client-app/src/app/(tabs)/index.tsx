import { useQuery } from '@tanstack/react-query';
import { ActivityIndicator, ScrollView, View, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { CategoryGrid } from '@/components/home/CategoryGrid';
import { ProximoTurnoCard } from '@/components/home/ProximoTurnoCard';
import { RutinaTeaser } from '@/components/home/RutinaTeaser';
import { TreatmentRow } from '@/components/home/TreatmentRow';
import { AppText } from '@/components/ui/AppText';
import { SearchBar } from '@/components/ui/SearchBar';
import { getServicios } from '@/services/public';
import { getMiRutina } from '@/services/rutina';
import { useAuthStore } from '@/stores/auth';
import { colors, fonts, radius, spacing } from '@/theme/ame';
import { formatFechaTurno, formatPrecio } from '@/utils/format';

export default function Inicio() {
  const usuario = useAuthStore((s) => s.usuario);
  const nombre = usuario?.nombre?.trim() || 'Bienvenida';
  const inicial = (usuario?.nombre || usuario?.email || '?').trim().charAt(0).toUpperCase();

  const serviciosQuery = useQuery({
    queryKey: ['servicios'],
    queryFn: () => getServicios(),
  });

  const miRutinaQuery = useQuery({
    queryKey: ['mi-rutina'],
    queryFn: () => getMiRutina(),
  });

  const plan = miRutinaQuery.data?.plan ?? null;
  const rutina = miRutinaQuery.data?.rutina ?? null;
  const servicios = serviciosQuery.data?.results ?? [];

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.header}>
        <View>
          <AppText variant="label">Hola de nuevo</AppText>
          <AppText variant="title" style={styles.name}>
            {nombre}
          </AppText>
        </View>
        <View style={styles.avatar}>
          <AppText style={styles.avatarTxt}>{inicial}</AppText>
        </View>
      </View>

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}>
        <SearchBar />

        {plan?.proximo_turno ? (
          <ProximoTurnoCard
            servicio={plan.tratamiento_sugerido || 'Tu próximo turno'}
            fecha={formatFechaTurno(plan.proximo_turno)}
          />
        ) : null}

        {rutina ? <RutinaTeaser rutina={rutina} /> : null}

        <View>
          <AppText variant="section" style={styles.sectionTitle}>
            Categorías
          </AppText>
          <CategoryGrid />
        </View>

        <View>
          <View style={styles.sectionRow}>
            <AppText variant="section">Tratamientos</AppText>
            <AppText variant="meta">Ver todos</AppText>
          </View>

          {serviciosQuery.isLoading ? (
            <ActivityIndicator color={colors.muted} style={styles.loader} />
          ) : serviciosQuery.isError ? (
            <AppText variant="meta">No pudimos cargar los tratamientos.</AppText>
          ) : servicios.length === 0 ? (
            <AppText variant="meta">Todavía no hay tratamientos disponibles.</AppText>
          ) : (
            <View style={styles.list}>
              {servicios.map((s) => (
                <TreatmentRow
                  key={s.id}
                  nombre={s.nombre}
                  meta={`${s.duracion_minutos} min${s.categoria_nombre ? ` · ${s.categoria_nombre}` : ''}`}
                  precio={formatPrecio(s.precio)}
                />
              ))}
            </View>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.ivory },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.xl,
    paddingTop: spacing.sm,
    paddingBottom: 14,
  },
  name: { marginTop: 4 },
  avatar: {
    width: 36,
    height: 36,
    borderRadius: radius.pill,
    backgroundColor: colors.blush,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarTxt: { fontFamily: fonts.serif, fontSize: 15, color: '#8a6f68' },
  scroll: { flex: 1 },
  content: { paddingHorizontal: spacing.xl, paddingBottom: spacing.xxl, gap: spacing.lg },
  sectionTitle: { marginBottom: spacing.md },
  sectionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'baseline',
    marginBottom: spacing.md,
  },
  loader: { marginTop: spacing.sm, alignSelf: 'flex-start' },
  list: { gap: spacing.md },
});
