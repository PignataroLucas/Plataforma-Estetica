import { Feather } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';
import { router } from 'expo-router';
import { useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { AppText } from '@/components/ui/AppText';
import { Card } from '@/components/ui/Card';
import { RutinaItemRow } from '@/components/rutina/RutinaItemRow';
import { SemanaRutina } from '@/components/rutina/SemanaRutina';
import { useMarcarPaso } from '@/hooks/useMarcarPaso';
import { getMiRutina } from '@/services/rutina';
import { colors, fonts, radius, spacing } from '@/theme/ame';
import type { MomentoRutina, PlanApp, RutinaApp, RutinaHoy } from '@/types/api';
import { formatFechaTurno } from '@/utils/format';
import { fechaLarga, rutinaDeHoyCompleta } from '@/utils/rutina';

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
          <AppText variant="meta" style={styles.fecha}>
            {data?.hoy ? `${fechaLarga(data.hoy.fecha)} · ` : ''}
            {data?.centro.nombre}
          </AppText>

          {data?.rutina ? (
            <RutinaContenido rutina={data.rutina} hoy={data.hoy} />
          ) : (
            <VacioRutina />
          )}

          {data?.plan ? <PlanCard plan={data.plan} /> : null}
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

function RutinaContenido({ rutina, hoy }: { rutina: RutinaApp; hoy: RutinaHoy | null }) {
  // Rutinas viejas sin items estructurados: caemos al texto libre legacy.
  if (rutina.items.length === 0 || !hoy) {
    return <RutinaLegacy rutina={rutina} />;
  }

  const noVanHoy = rutina.items.filter((i) => !i.va_hoy);

  return (
    <View style={styles.secciones}>
      {rutinaDeHoyCompleta(hoy) ? <Felicitacion racha={hoy.racha} /> : null}

      <Card style={styles.semana}>
        <View style={styles.semanaTop}>
          <AppText variant="label">Esta semana</AppText>
          <Racha dias={hoy.racha} />
        </View>
        <SemanaRutina hoy={hoy} variante="dias" />
      </Card>

      <Seccion titulo="De día" icon="sun" momento="DIURNA" rutina={rutina} hoy={hoy} />
      <Seccion titulo="De noche" icon="moon" momento="NOCTURNA" rutina={rutina} hoy={hoy} />

      {noVanHoy.length > 0 ? (
        <View style={styles.seccion}>
          <View style={styles.secHead}>
            <Feather name="calendar" size={15} color={colors.muted} />
            <AppText variant="label">No van hoy</AppText>
          </View>
          <View style={styles.items}>
            {noVanHoy.map((item, i) => (
              <RutinaItemRow key={item.id} item={item} index={i + 1} />
            ))}
          </View>
        </View>
      ) : null}
    </View>
  );
}

function Racha({ dias }: { dias: number }) {
  if (dias === 0) return <AppText variant="meta">Empezá hoy tu racha</AppText>;
  return (
    <View style={styles.racha}>
      <AppText style={styles.rachaNum}>{dias}</AppText>
      <AppText variant="meta">{dias === 1 ? 'día' : 'días seguidos'}</AppText>
    </View>
  );
}

function Felicitacion({ racha }: { racha: number }) {
  return (
    <View style={styles.felicitacion}>
      <View style={styles.felicitacionIcon}>
        <Feather name="check" size={17} color={colors.onDark} />
      </View>
      <View style={styles.felicitacionTxt}>
        <AppText variant="cardTitle" color={colors.onDark}>
          Completaste tu rutina de hoy
        </AppText>
        <AppText variant="meta" color={colors.onDarkMuted}>
          {racha > 1 ? `${racha} días seguidos. Nos vemos mañana.` : 'Nos vemos mañana.'}
        </AppText>
      </View>
    </View>
  );
}

function Seccion({
  titulo,
  icon,
  momento,
  rutina,
  hoy,
}: {
  titulo: string;
  icon: 'sun' | 'moon';
  momento: MomentoRutina;
  rutina: RutinaApp;
  hoy: RutinaHoy;
}) {
  const marcar = useMarcarPaso();
  // Una sección cumplida se pliega para dejar a la vista lo que falta; la
  // clienta puede abrirla para revisar o destildar.
  const [abierta, setAbierta] = useState(false);

  const items = rutina.items.filter((i) => i.momento === momento && i.va_hoy);
  if (items.length === 0) return null;

  const { hechos, total, cumplido } = hoy.momentos[momento];
  const hechosSet = new Set(hoy.pasos_hechos);
  const plegada = cumplido && !abierta;

  return (
    <View style={styles.seccion}>
      <View style={styles.secHead}>
        <Feather name={icon} size={16} color={colors.ink} />
        <AppText variant="section" style={styles.secTitulo}>
          {titulo}
        </AppText>
        {cumplido ? (
          <View style={styles.lista}>
            <Feather name="check" size={12} color={colors.ink} />
            <AppText style={styles.contador}>Lista</AppText>
          </View>
        ) : (
          <AppText style={[styles.contador, styles.contadorPendiente]}>
            {hechos} de {total}
          </AppText>
        )}
      </View>
      <View style={styles.barra}>
        <View style={[styles.barraLlena, { width: `${Math.round((hechos / total) * 100)}%` }]} />
      </View>

      {plegada ? null : (
        <View style={styles.items}>
          {items.map((item) => {
            const hecho = hechosSet.has(item.id);
            return (
              <RutinaItemRow
                key={item.id}
                item={item}
                hecho={hecho}
                onToggle={() => {
                  marcar.mutate({ item, hecho: !hecho });
                  // Con el último tilde la sección se pliega sola.
                  if (!hecho && hechos + 1 === total) setAbierta(false);
                }}
              />
            );
          })}
        </View>
      )}

      {cumplido ? (
        <Pressable
          onPress={() => setAbierta((v) => !v)}
          style={styles.plegar}
          accessibilityRole="button"
          hitSlop={6}>
          <AppText style={styles.plegarTxt}>{plegada ? `Ver los ${total} pasos` : 'Plegar'}</AppText>
          <Feather name={plegada ? 'chevron-down' : 'chevron-up'} size={14} color={colors.ink} />
        </Pressable>
      ) : null}

      {marcar.isError ? (
        <AppText variant="meta" color={colors.danger}>
          No pudimos guardar el último paso. Revisá tu conexión y probá de nuevo.
        </AppText>
      ) : null}
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
  fecha: { textAlign: 'center', marginTop: -spacing.sm },

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

  secciones: { gap: 26 },
  seccion: { gap: spacing.md },
  secHead: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  secTitulo: { flex: 1 },
  items: { gap: spacing.lg, marginTop: spacing.xs },
  contador: { fontFamily: fonts.sansMedium, fontSize: 11, color: colors.ink },
  contadorPendiente: { color: colors.muted },
  lista: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  barra: { height: 2, borderRadius: 2, backgroundColor: colors.line, overflow: 'hidden' },
  barraLlena: { height: '100%', backgroundColor: colors.ink },
  plegar: {
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    minHeight: 36,
    paddingHorizontal: 14,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.pill,
    backgroundColor: colors.card,
  },
  plegarTxt: { fontFamily: fonts.sans, fontSize: 12, color: colors.ink },

  semana: { gap: spacing.md, borderRadius: radius.lg },
  semanaTop: { flexDirection: 'row', alignItems: 'baseline', justifyContent: 'space-between' },
  racha: { flexDirection: 'row', alignItems: 'baseline', gap: 5 },
  rachaNum: { fontFamily: fonts.serif, fontSize: 22, lineHeight: 24, color: colors.ink },

  felicitacion: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    backgroundColor: '#171310',
    borderRadius: radius.lg,
    padding: spacing.lg,
  },
  felicitacionIcon: {
    width: 40,
    height: 40,
    borderRadius: radius.pill,
    backgroundColor: 'rgba(232,209,205,0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  felicitacionTxt: { flex: 1, minWidth: 0, gap: 2 },

  legacyTxt: { lineHeight: 22 },
  legacyProd: { lineHeight: 18 },

  vacio: { alignItems: 'center', gap: spacing.sm, paddingVertical: spacing.xxl, paddingHorizontal: spacing.lg },
  vacioTitulo: { marginTop: spacing.sm },
  vacioTxt: { textAlign: 'center', lineHeight: 17 },
});
