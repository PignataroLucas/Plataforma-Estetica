import { Feather } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';
import { router } from 'expo-router';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { AppText } from '@/components/ui/AppText';
import { Card } from '@/components/ui/Card';
import { RutinaItemRow } from '@/components/rutina/RutinaItemRow';
import { getMiRutina } from '@/services/rutina';
import { colors, radius, spacing } from '@/theme/ame';
import type { PlanApp, RutinaApp } from '@/types/api';
import { formatFechaTurno } from '@/utils/format';

export default function MiRutinaScreen() {
  const { data, isLoading, isError, refetch, isRefetching } = useQuery({
    queryKey: ['mi-rutina'],
    queryFn: () => getMiRutina(),
  });

  const volver = () => {
    if (router.canGoBack()) router.back();
    else router.replace('/');
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
      <View style={styles.header}>
        <Pressable onPress={volver} hitSlop={12} style={styles.back} accessibilityRole="button">
          <Feather name="chevron-left" size={22} color={colors.ink} />
        </Pressable>
        <AppText variant="section">Mi rutina</AppText>
        <View style={styles.back} />
      </View>

      {isLoading ? (
        <View style={styles.center}>
          <ActivityIndicator color={colors.muted} />
        </View>
      ) : isError ? (
        <View style={styles.center}>
          <AppText variant="body" color={colors.muted} style={styles.centerText}>
            No pudimos cargar tu rutina.
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
          showsVerticalScrollIndicator={false}>
          <AppText variant="meta">{data?.centro.nombre}</AppText>

          {data?.plan ? <PlanCard plan={data.plan} /> : null}

          {data?.rutina ? (
            <RutinaContenido rutina={data.rutina} />
          ) : (
            <VacioRutina />
          )}
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

function PlanCard({ plan }: { plan: PlanApp }) {
  const meta = [plan.frecuencia, plan.sesiones_estimadas ? `${plan.sesiones_estimadas} sesiones` : null]
    .filter(Boolean)
    .join(' · ');

  return (
    <Card style={styles.plan}>
      <AppText variant="label">Tu plan</AppText>
      <AppText variant="cardTitle" style={styles.planTitulo}>
        {plan.tratamiento_sugerido}
      </AppText>
      {meta ? <AppText variant="meta">{meta}</AppText> : null}

      {plan.proximo_turno ? (
        <View style={styles.turnoRow}>
          <Feather name="calendar" size={14} color={colors.ink} />
          <AppText variant="body">{formatFechaTurno(plan.proximo_turno)}</AppText>
        </View>
      ) : null}

      {plan.indicaciones ? (
        <View style={styles.indicaciones}>
          <AppText variant="label" style={styles.indicacionesLabel}>
            Indicaciones
          </AppText>
          <AppText variant="body" color={colors.muted} style={styles.indicacionesTxt}>
            {plan.indicaciones}
          </AppText>
        </View>
      ) : null}
    </Card>
  );
}

function RutinaContenido({ rutina }: { rutina: RutinaApp }) {
  const dia = rutina.items.filter((i) => i.momento === 'DIURNA');
  const noche = rutina.items.filter((i) => i.momento === 'NOCTURNA');

  // Rutinas viejas sin items estructurados: caemos al texto libre legacy.
  if (rutina.items.length === 0) {
    return <RutinaLegacy rutina={rutina} />;
  }

  return (
    <View style={styles.secciones}>
      <Seccion titulo="De día" icon="sun" items={dia} />
      <Seccion titulo="De noche" icon="moon" items={noche} />
    </View>
  );
}

function Seccion({
  titulo,
  icon,
  items,
}: {
  titulo: string;
  icon: 'sun' | 'moon';
  items: RutinaApp['items'];
}) {
  if (items.length === 0) return null;
  return (
    <View style={styles.seccion}>
      <View style={styles.secHead}>
        <Feather name={icon} size={16} color={colors.ink} />
        <AppText variant="section">{titulo}</AppText>
      </View>
      <View style={styles.items}>
        {items.map((item, i) => (
          <RutinaItemRow key={item.id} item={item} index={i + 1} />
        ))}
      </View>
    </View>
  );
}

function RutinaLegacy({ rutina }: { rutina: RutinaApp }) {
  const bloques = [
    { titulo: 'De día', icon: 'sun' as const, pasos: rutina.rutina_diurna_pasos, productos: rutina.rutina_diurna_productos },
    { titulo: 'De noche', icon: 'moon' as const, pasos: rutina.rutina_nocturna_pasos, productos: rutina.rutina_nocturna_productos },
  ].filter((b) => b.pasos || b.productos);

  if (bloques.length === 0) return <VacioRutina />;

  return (
    <View style={styles.secciones}>
      {bloques.map((b) => (
        <View key={b.titulo} style={styles.seccion}>
          <View style={styles.secHead}>
            <Feather name={b.icon} size={16} color={colors.ink} />
            <AppText variant="section">{b.titulo}</AppText>
          </View>
          {b.pasos ? (
            <AppText variant="body" color={colors.ink} style={styles.legacyTxt}>
              {b.pasos}
            </AppText>
          ) : null}
          {b.productos ? (
            <AppText variant="meta" style={styles.legacyProd}>
              {b.productos}
            </AppText>
          ) : null}
        </View>
      ))}
    </View>
  );
}

function VacioRutina() {
  return (
    <View style={styles.vacio}>
      <Feather name="feather" size={26} color={colors.taupe} />
      <AppText variant="cardTitle" style={styles.vacioTitulo}>
        Todavía no tenés una rutina
      </AppText>
      <AppText variant="meta" style={styles.vacioTxt}>
        Cuando tu profesional cargue tu rutina de cuidado, la vas a ver acá.
      </AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.ivory },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.md,
  },
  back: { width: 40, height: 40, justifyContent: 'center' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: spacing.md, padding: spacing.xl },
  centerText: { textAlign: 'center' },
  retry: { paddingVertical: spacing.sm, paddingHorizontal: spacing.lg, borderWidth: 1, borderColor: colors.line, borderRadius: radius.md },
  content: { paddingHorizontal: spacing.xl, paddingBottom: spacing.xxl, gap: spacing.xl },

  plan: { gap: 5 },
  planTitulo: { marginTop: 4, lineHeight: 21 },
  turnoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginTop: spacing.md,
    paddingTop: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.line,
  },
  indicaciones: { marginTop: spacing.md, gap: 4 },
  indicacionesLabel: { marginLeft: 0 },
  indicacionesTxt: { lineHeight: 20 },

  secciones: { gap: spacing.xl },
  seccion: { gap: spacing.lg },
  secHead: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  items: { gap: spacing.lg },

  legacyTxt: { lineHeight: 22 },
  legacyProd: { lineHeight: 18 },

  vacio: { alignItems: 'center', gap: spacing.sm, paddingVertical: spacing.xxl, paddingHorizontal: spacing.lg },
  vacioTitulo: { marginTop: spacing.sm },
  vacioTxt: { textAlign: 'center', lineHeight: 17 },
});
