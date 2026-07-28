import { Feather } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';
import { router, useLocalSearchParams } from 'expo-router';
import { useMemo, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { TreatmentRow } from '@/components/home/TreatmentRow';
import { AppText } from '@/components/ui/AppText';
import { SearchBar } from '@/components/ui/SearchBar';
import { useCentroActivo } from '@/hooks/useCentroActivo';
import { getServicios } from '@/services/public';
import { colors, radius, spacing } from '@/theme/ame';
import type { ServicioPublico } from '@/types/api';
import { formatPrecio } from '@/utils/format';

const TODAS = '__todas__';

/**
 * Catálogo completo de tratamientos. Es a donde llevan "Ver todos" y los cuadros
 * de Categorías de Inicio; cada fila abre la ficha del tratamiento.
 */
export default function ServiciosScreen() {
  // Inicio puede llegar con una categoría ya elegida desde la grilla.
  const { categoria } = useLocalSearchParams<{ categoria?: string }>();
  const { centroId } = useCentroActivo();

  const [busqueda, setBusqueda] = useState('');
  const [filtro, setFiltro] = useState<string>(categoria ?? TODAS);

  const { data, isPending, isError, refetch } = useQuery({
    queryKey: ['servicios', centroId],
    queryFn: () => getServicios(centroId),
  });

  const servicios = useMemo(() => data?.results ?? [], [data]);

  const categorias = useMemo(() => {
    const nombres = servicios
      .map((s) => s.categoria_nombre)
      .filter((n): n is string => Boolean(n));
    return Array.from(new Set(nombres)).sort((a, b) => a.localeCompare(b, 'es'));
  }, [servicios]);

  const visibles = useMemo(() => {
    const texto = busqueda.trim().toLowerCase();
    return servicios.filter((s) => {
      const porCategoria = filtro === TODAS || s.categoria_nombre === filtro;
      const porTexto =
        !texto ||
        s.nombre.toLowerCase().includes(texto) ||
        s.descripcion.toLowerCase().includes(texto);
      return porCategoria && porTexto;
    });
  }, [servicios, filtro, busqueda]);

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
        <AppText variant="section">Tratamientos</AppText>
        <View style={styles.back} />
      </View>

      {isPending ? (
        <View style={styles.center}>
          <ActivityIndicator color={colors.muted} />
        </View>
      ) : isError ? (
        <View style={styles.center}>
          <AppText variant="body" color={colors.muted} style={styles.centerTxt}>
            No pudimos cargar los tratamientos.
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
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled">
          <SearchBar value={busqueda} onChangeText={setBusqueda} />

          {categorias.length > 0 ? (
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.chips}>
              <Chip label="Todos" activo={filtro === TODAS} onPress={() => setFiltro(TODAS)} />
              {categorias.map((c) => (
                <Chip key={c} label={c} activo={filtro === c} onPress={() => setFiltro(c)} />
              ))}
            </ScrollView>
          ) : null}

          {visibles.length === 0 ? (
            <Vacio conFiltro={busqueda.trim() !== '' || filtro !== TODAS} />
          ) : (
            <View style={styles.lista}>
              {visibles.map((s) => (
                <TreatmentRow
                  key={s.id}
                  nombre={s.nombre}
                  meta={metaDe(s)}
                  precio={formatPrecio(s.precio)}
                  onPress={() => router.push(`/servicio/${s.id}`)}
                />
              ))}
            </View>
          )}
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

function Chip({
  label,
  activo,
  onPress,
}: {
  label: string;
  activo: boolean;
  onPress: () => void;
}) {
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityState={{ selected: activo }}
      style={[styles.chip, activo && styles.chipActivo]}>
      <AppText variant="meta" color={activo ? colors.onDark : colors.ink}>
        {label}
      </AppText>
    </Pressable>
  );
}

function Vacio({ conFiltro }: { conFiltro: boolean }) {
  return (
    <View style={styles.vacio}>
      <Feather name="search" size={24} color={colors.taupe} />
      <AppText variant="cardTitle" style={styles.vacioTitulo}>
        {conFiltro ? 'Sin resultados' : 'Todavía no hay tratamientos'}
      </AppText>
      <AppText variant="meta" style={styles.vacioTxt}>
        {conFiltro
          ? 'Probá con otra búsqueda o mirá todas las categorías.'
          : 'Cuando el centro cargue su catálogo, lo vas a ver acá.'}
      </AppText>
    </View>
  );
}

function metaDe(servicio: ServicioPublico): string {
  return [`${servicio.duracion_minutos} min`, servicio.categoria_nombre]
    .filter(Boolean)
    .join(' · ');
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
  centerTxt: { textAlign: 'center' },
  retry: {
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.lg,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
  },
  content: { paddingHorizontal: spacing.xl, paddingBottom: spacing.xxl, gap: spacing.lg },

  chips: { gap: spacing.sm, paddingRight: spacing.xl },
  chip: {
    paddingVertical: 7,
    paddingHorizontal: 14,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.card,
  },
  chipActivo: { backgroundColor: colors.ink, borderColor: colors.ink },

  lista: { gap: spacing.md },
  vacio: { alignItems: 'center', gap: spacing.sm, paddingVertical: spacing.xxl },
  vacioTitulo: { marginTop: spacing.sm },
  vacioTxt: { textAlign: 'center', lineHeight: 17 },
});
