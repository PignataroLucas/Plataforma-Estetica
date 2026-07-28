import { useQuery } from '@tanstack/react-query';
import { router } from 'expo-router';
import { useMemo } from 'react';
import { ActivityIndicator, Pressable, ScrollView, View, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { CategoryGrid } from '@/components/home/CategoryGrid';
import { ProximoTurnoCard } from '@/components/home/ProximoTurnoCard';
import { RutinaTeaser } from '@/components/home/RutinaTeaser';
import { TreatmentRow } from '@/components/home/TreatmentRow';
import { AppText } from '@/components/ui/AppText';
import { SearchBar } from '@/components/ui/SearchBar';
import { useCentroActivo } from '@/hooks/useCentroActivo';
import { getServicios } from '@/services/public';
import { getMiRutina } from '@/services/rutina';
import { getMisTurnos } from '@/services/turnos';
import { useAuthStore } from '@/stores/auth';
import { colors, fonts, radius, spacing } from '@/theme/ame';
import { formatFechaTurno, formatPrecio } from '@/utils/format';

/** Tratamientos que se muestran en Inicio antes de mandar al catálogo completo. */
const MAX_DESTACADOS = 4;

export default function Inicio() {
  const usuario = useAuthStore((s) => s.usuario);
  const { centroId } = useCentroActivo();
  const nombre = usuario?.nombre?.trim() || 'Bienvenida';
  const inicial = (usuario?.nombre || usuario?.email || '?').trim().charAt(0).toUpperCase();

  // Mismo centro y misma queryKey que el catálogo: se comparte la caché.
  const serviciosQuery = useQuery({
    queryKey: ['servicios', centroId],
    queryFn: () => getServicios(centroId),
  });

  const miRutinaQuery = useQuery({
    queryKey: ['mi-rutina'],
    queryFn: () => getMiRutina(),
  });

  const turnosQuery = useQuery({
    queryKey: ['mis-turnos'],
    queryFn: () => getMisTurnos(),
  });

  const plan = miRutinaQuery.data?.plan ?? null;
  const rutina = miRutinaQuery.data?.rutina ?? null;
  const servicios = serviciosQuery.data?.results ?? [];
  // Inicio muestra un adelanto; el catálogo completo vive en /servicios.
  const destacados = servicios.slice(0, MAX_DESTACADOS);
  const categorias = useMemo(() => {
    const nombres = servicios
      .map((s) => s.categoria_nombre)
      .filter((n): n is string => Boolean(n));
    return Array.from(new Set(nombres)).sort((a, b) => a.localeCompare(b, 'es'));
  }, [servicios]);
  // El turno real manda; el próximo turno del plan es el fallback que carga el staff.
  const proximoTurno = turnosQuery.data?.proximos[0] ?? null;

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

        {proximoTurno ? (
          <Pressable onPress={() => router.push('/turnos')} accessibilityRole="button">
            <ProximoTurnoCard
              servicio={proximoTurno.servicio_nombre}
              fecha={formatFechaTurno(proximoTurno.fecha_hora_inicio)}
              profesional={proximoTurno.profesional_nombre ?? undefined}
            />
          </Pressable>
        ) : plan?.proximo_turno ? (
          <ProximoTurnoCard
            servicio={plan.tratamiento_sugerido || 'Tu próximo turno'}
            fecha={formatFechaTurno(plan.proximo_turno)}
          />
        ) : null}

        {rutina ? <RutinaTeaser rutina={rutina} /> : null}

        {categorias.length > 0 ? (
          <View>
            <AppText variant="section" style={styles.sectionTitle}>
              Categorías
            </AppText>
            <CategoryGrid categorias={categorias} />
          </View>
        ) : null}

        <View>
          <View style={styles.sectionRow}>
            <AppText variant="section">Tratamientos</AppText>
            <Pressable onPress={() => router.push('/servicios')} hitSlop={8} accessibilityRole="button">
              <AppText variant="meta">Ver todos</AppText>
            </Pressable>
          </View>

          {serviciosQuery.isLoading ? (
            <ActivityIndicator color={colors.muted} style={styles.loader} />
          ) : serviciosQuery.isError ? (
            <AppText variant="meta">No pudimos cargar los tratamientos.</AppText>
          ) : servicios.length === 0 ? (
            <AppText variant="meta">Todavía no hay tratamientos disponibles.</AppText>
          ) : (
            <View style={styles.list}>
              {destacados.map((s) => (
                <TreatmentRow
                  key={s.id}
                  nombre={s.nombre}
                  meta={`${s.duracion_minutos} min${s.categoria_nombre ? ` · ${s.categoria_nombre}` : ''}`}
                  precio={formatPrecio(s.precio)}
                  onPress={() => router.push(`/servicio/${s.id}`)}
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
