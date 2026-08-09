import { Feather } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';
import * as Linking from 'expo-linking';
import { router, useLocalSearchParams } from 'expo-router';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { AppText } from '@/components/ui/AppText';
import { Button } from '@/components/ui/Button';
import { useCentroActivo } from '@/hooks/useCentroActivo';
import { getCentroInfo, getServicio } from '@/services/public';
import { colors, radius, spacing } from '@/theme/ame';
import type { ServicioPublico } from '@/types/api';
import { formatFechaChip, formatPrecio, parsearBeneficios } from '@/utils/format';

/** Cuántas fechas puntuales se muestran en la ficha antes del "+N más". */
const MAX_FECHAS_FICHA = 4;

/**
 * Ficha del tratamiento: lo que el centro escribe en el CRM (qué es, beneficios,
 * link de video) más el CTA. Es pantalla de stack, no tab: se llega desde el
 * catálogo o desde Inicio, y desde acá se entra a Reservar con el servicio elegido.
 */
export default function FichaServicioScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const servicioId = Number(id);
  const { centroId } = useCentroActivo();

  const { data, isPending, isError, refetch } = useQuery({
    queryKey: ['servicio', servicioId, centroId],
    queryFn: () => getServicio(servicioId, centroId),
    enabled: Number.isFinite(servicioId),
  });

  const volver = () => {
    if (router.canGoBack()) router.back();
    else router.replace('/servicios');
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
      <View style={styles.header}>
        <Pressable onPress={volver} hitSlop={12} style={styles.back} accessibilityRole="button">
          <Feather name="chevron-left" size={22} color={colors.ink} />
        </Pressable>
        <AppText variant="section">Tratamiento</AppText>
        <View style={styles.back} />
      </View>

      {isPending ? (
        <View style={styles.center}>
          <ActivityIndicator color={colors.muted} />
        </View>
      ) : isError || !data ? (
        <View style={styles.center}>
          <AppText variant="body" color={colors.muted} style={styles.centerTxt}>
            No pudimos cargar este tratamiento.
          </AppText>
          <Pressable onPress={() => refetch()} hitSlop={8} style={styles.retry}>
            <AppText variant="meta" color={colors.ink}>
              Reintentar
            </AppText>
          </Pressable>
        </View>
      ) : (
        <Ficha servicio={data} />
      )}
    </SafeAreaView>
  );
}

function Ficha({ servicio }: { servicio: ServicioPublico }) {
  const beneficios = parsearBeneficios(servicio.beneficios);
  const sinContenido = !servicio.descripcion.trim() && beneficios.length === 0 && !servicio.video_url;

  return (
    <>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <Hero servicio={servicio} />

        {servicio.reservable_por_cliente && servicio.modo_reserva === 'fechas' ? (
          <ProximasFechas fechas={servicio.fechas_disponibles} />
        ) : null}

        {servicio.video_url ? <VideoRow url={servicio.video_url} /> : null}

        {servicio.descripcion.trim() ? (
          <Seccion titulo="Qué es">
            <AppText variant="body" style={styles.parrafo}>
              {servicio.descripcion.trim()}
            </AppText>
          </Seccion>
        ) : null}

        {beneficios.length > 0 ? (
          <Seccion titulo="Beneficios">
            <View style={styles.beneficios}>
              {beneficios.map((b) => (
                <View key={b} style={styles.beneficio}>
                  <View style={styles.bullet} />
                  <AppText variant="body" style={styles.beneficioTxt}>
                    {b}
                  </AppText>
                </View>
              ))}
            </View>
          </Seccion>
        ) : null}

        {sinContenido ? (
          <AppText variant="meta" style={styles.sinContenido}>
            Todavía no cargamos el detalle de este tratamiento. Escribinos y te contamos
            todo con gusto.
          </AppText>
        ) : null}
      </ScrollView>

      <View style={styles.footer}>
        <Cta servicio={servicio} />
      </View>
    </>
  );
}

function Hero({ servicio }: { servicio: ServicioPublico }) {
  return (
    <View style={styles.hero}>
      {servicio.categoria_nombre ? (
        <AppText variant="label">{servicio.categoria_nombre}</AppText>
      ) : null}
      <AppText variant="title" style={styles.heroNombre}>
        {servicio.nombre}
      </AppText>
      <View style={styles.heroMeta}>
        <View style={styles.metaItem}>
          <Feather name="clock" size={13} color={colors.muted} />
          <AppText variant="meta">{servicio.duracion_minutos} min</AppText>
        </View>
        <View style={styles.metaItem}>
          <Feather name="map-pin" size={13} color={colors.muted} />
          <AppText variant="meta">{servicio.sucursal_nombre}</AppText>
        </View>
      </View>
      <AppText variant="title" style={styles.heroPrecio}>
        {formatPrecio(servicio.precio)}
      </AppText>
    </View>
  );
}

/**
 * Tratamientos sin patrón semanal (la máquina viene fechas sueltas): la clienta
 * ve las fechas acá, antes de entrar al flujo de reserva y encontrarse con un
 * calendario casi vacío.
 */
function ProximasFechas({ fechas }: { fechas: string[] }) {
  if (fechas.length === 0) {
    return (
      <View style={styles.seccion}>
        <AppText variant="section">Próximas fechas</AppText>
        <AppText variant="meta" style={styles.parrafoCorto}>
          Todavía no hay fechas abiertas para este tratamiento. Consultanos y te
          avisamos apenas se agenda la próxima.
        </AppText>
      </View>
    );
  }

  const visibles = fechas.slice(0, MAX_FECHAS_FICHA);
  const restantes = fechas.length - visibles.length;

  return (
    <View style={styles.seccion}>
      <AppText variant="section">Próximas fechas</AppText>
      <View style={styles.fechas}>
        {visibles.map((iso) => (
          <View key={iso} style={styles.fechaChip}>
            <Feather name="calendar" size={12} color={colors.ink} />
            <AppText variant="meta" color={colors.ink}>
              {formatFechaChip(iso)}
            </AppText>
          </View>
        ))}
        {restantes > 0 ? (
          <AppText variant="meta" style={styles.fechasMas}>
            +{restantes} más
          </AppText>
        ) : null}
      </View>
    </View>
  );
}

function VideoRow({ url }: { url: string }) {
  return (
    <Pressable
      onPress={() => Linking.openURL(url)}
      accessibilityRole="link"
      style={({ pressed }) => [styles.video, pressed && styles.videoPresionado]}>
      <View style={styles.play}>
        <Feather name="play" size={14} color={colors.onDark} />
      </View>
      <View style={styles.flex}>
        <AppText variant="cardTitle" style={styles.videoTitulo}>
          Mirá el tratamiento
        </AppText>
        <AppText variant="meta">Se abre el video</AppText>
      </View>
      <Feather name="external-link" size={16} color={colors.muted} />
    </Pressable>
  );
}

/**
 * "Reservar" solo si el centro habilitó el servicio para la app Y quedan fechas
 * por delante — un tratamiento de fechas puntuales que ya pasaron no tiene nada
 * que ofrecer, así que mejor mandar a hablar con el centro que a un calendario
 * vacío. Si no, el camino es WhatsApp cuando el teléfono es válido.
 */
function Cta({ servicio }: { servicio: ServicioPublico }) {
  const { centroId } = useCentroActivo();
  const puedeReservar =
    servicio.reservable_por_cliente && servicio.fechas_disponibles.length > 0;

  const { data: centro } = useQuery({
    queryKey: ['centro-info', centroId],
    queryFn: () => getCentroInfo(centroId),
    enabled: !puedeReservar,
  });

  if (puedeReservar) {
    return (
      <Button
        label="Reservar"
        onPress={() =>
          router.push({ pathname: '/reservar', params: { servicio: String(servicio.id) } })
        }
      />
    );
  }

  const whatsapp = centro?.telefono_whatsapp;

  if (!whatsapp) {
    return (
      <AppText variant="meta" style={styles.ctaTxt}>
        Este tratamiento se coordina directamente con el centro.
      </AppText>
    );
  }

  const mensaje = encodeURIComponent(`¡Hola! Quería consultar por ${servicio.nombre}.`);

  return (
    <Button
      label="Consultar con el centro"
      onPress={() => Linking.openURL(`https://wa.me/${whatsapp.replace('+', '')}?text=${mensaje}`)}
    />
  );
}

function Seccion({ titulo, children }: { titulo: string; children: React.ReactNode }) {
  return (
    <View style={styles.seccion}>
      <AppText variant="section">{titulo}</AppText>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.ivory },
  flex: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.md,
  },
  back: { width: 40, height: 40, justifyContent: 'center' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: spacing.md, padding: spacing.xl },
  centerTxt: { textAlign: 'center' },
  retry: {
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.lg,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
  },
  content: { paddingHorizontal: spacing.xl, paddingBottom: spacing.xxl, gap: spacing.xl },

  // Sin foto, el peso visual lo lleva el bloque crema con la tipografía serif.
  hero: {
    backgroundColor: colors.cream,
    borderRadius: radius.lg,
    padding: spacing.xl,
    gap: spacing.sm,
  },
  heroNombre: { fontSize: 27, lineHeight: 32 },
  heroMeta: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.lg, marginTop: 2 },
  metaItem: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  heroPrecio: { fontSize: 24, marginTop: spacing.sm },

  video: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    paddingVertical: 13,
    paddingHorizontal: spacing.lg,
  },
  videoPresionado: { backgroundColor: colors.cream },
  videoTitulo: { fontSize: 16, lineHeight: 19 },
  play: {
    width: 34,
    height: 34,
    borderRadius: radius.pill,
    backgroundColor: colors.ink,
    alignItems: 'center',
    justifyContent: 'center',
  },

  seccion: { gap: spacing.md },
  parrafo: { lineHeight: 22 },
  parrafoCorto: { lineHeight: 18 },

  fechas: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: spacing.sm },
  fechaChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: colors.cream,
    borderRadius: radius.pill,
    paddingVertical: 6,
    paddingHorizontal: spacing.md,
  },
  fechasMas: { paddingHorizontal: spacing.xs },

  beneficios: { gap: spacing.md },
  beneficio: { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.md },
  bullet: {
    width: 5,
    height: 5,
    borderRadius: radius.pill,
    backgroundColor: colors.blush,
    marginTop: 7,
  },
  beneficioTxt: { flex: 1, lineHeight: 21 },
  sinContenido: { lineHeight: 18 },

  footer: {
    paddingHorizontal: spacing.xl,
    paddingTop: spacing.md,
    paddingBottom: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.line,
    backgroundColor: colors.ivory,
  },
  ctaTxt: { textAlign: 'center', lineHeight: 17, paddingVertical: spacing.md },
});
