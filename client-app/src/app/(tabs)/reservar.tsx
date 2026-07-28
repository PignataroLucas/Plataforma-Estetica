import { Feather } from '@expo/vector-icons';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { router, useLocalSearchParams } from 'expo-router';
import { useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { DateStrip } from '@/components/reservar/DateStrip';
import { SlotGrid } from '@/components/reservar/SlotGrid';
import { AppText } from '@/components/ui/AppText';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Field } from '@/components/ui/Field';
import { useCentroActivo } from '@/hooks/useCentroActivo';
import { ApiError } from '@/services/api';
import { getDisponibilidad, getServiciosReservables, reservarTurno } from '@/services/turnos';
import { colors, radius, spacing } from '@/theme/ame';
import type { ServicioReservable, SlotDisponible, TurnoApp } from '@/types/api';
import {
  fechaISOLocal,
  formatDiasReserva,
  formatFechaLarga,
  formatPrecio,
  nombreDiaBackend,
  parseFechaISOLocal,
} from '@/utils/format';

/** Cantidad de días reservables que ofrece el selector. */
const DIAS_A_MOSTRAR = 30;
/** Tope de días a recorrer buscando fechas válidas (evita loops si algo viene mal). */
const VENTANA_MAXIMA = 90;

type Paso = 1 | 2 | 3;

export default function ReservarScreen() {
  const { centroId, centroNombre } = useCentroActivo();
  const queryClient = useQueryClient();
  // La ficha del tratamiento entra acá con el servicio ya elegido.
  const { servicio: servicioParam } = useLocalSearchParams<{ servicio?: string }>();

  const [paso, setPaso] = useState<Paso>(1);
  const [servicio, setServicio] = useState<ServicioReservable | null>(null);
  const [fecha, setFecha] = useState('');
  const [slot, setSlot] = useState<SlotDisponible | null>(null);
  const [notas, setNotas] = useState('');
  const [reservado, setReservado] = useState<TurnoApp | null>(null);
  const [error, setError] = useState<string | null>(null);

  const serviciosQuery = useQuery({
    queryKey: ['servicios-reservables', centroId],
    queryFn: () => getServiciosReservables(centroId),
  });

  const primeraFecha = serviciosQuery.data?.primera_fecha;

  /**
   * Preselección desde la ficha. Se consume una sola vez: si después el usuario
   * vuelve al paso 1 a cambiar de tratamiento, el parámetro no lo arrastra de nuevo.
   * Si el id no está entre los reservables, se ignora y arranca en el paso 1.
   */
  const paramConsumido = useRef(false);
  useEffect(() => {
    if (paramConsumido.current || !servicioParam) return;
    const resultados = serviciosQuery.data?.results;
    if (!resultados) return;

    paramConsumido.current = true;
    const elegido = resultados.find((s) => s.id === Number(servicioParam));
    if (elegido) {
      setServicio(elegido);
      setPaso(2);
    }
  }, [servicioParam, serviciosQuery.data]);

  /**
   * Días que se pueden elegir: desde la primera fecha reservable que informa el
   * backend (nunca hoy) y solo los días habilitados para ESE servicio. Se muestran
   * únicamente los válidos, en vez de pintar días deshabilitados.
   */
  const dias = useMemo(() => {
    if (!servicio || !primeraFecha) return [];
    const permitidos = new Set(servicio.dias_reserva);
    const cursor = parseFechaISOLocal(primeraFecha);
    const validos: Date[] = [];

    for (let i = 0; i < VENTANA_MAXIMA && validos.length < DIAS_A_MOSTRAR; i += 1) {
      const dia = new Date(cursor);
      dia.setDate(cursor.getDate() + i);
      if (permitidos.has(nombreDiaBackend(dia))) validos.push(dia);
    }
    return validos;
  }, [servicio, primeraFecha]);

  // Al cambiar de servicio, la fecha elegida puede no ser válida para el nuevo.
  useEffect(() => {
    if (dias.length === 0) return;
    const disponibles = dias.map(fechaISOLocal);
    if (!disponibles.includes(fecha)) {
      setFecha(disponibles[0]);
      setSlot(null);
    }
  }, [dias, fecha]);

  const disponibilidad = useQuery({
    queryKey: ['disponibilidad', servicio?.id, fecha],
    queryFn: () => getDisponibilidad(servicio!.id, fecha),
    enabled: servicio !== null && fecha !== '',
  });

  const reserva = useMutation({
    mutationFn: () =>
      reservarTurno({
        servicio: servicio!.id,
        fecha_hora_inicio: slot!.inicio,
        notas: notas.trim(),
      }),
    onSuccess: (turno) => {
      setError(null);
      setReservado(turno);
      queryClient.invalidateQueries({ queryKey: ['mis-turnos'] });
      queryClient.invalidateQueries({ queryKey: ['disponibilidad'] });
    },
    onError: (err) => {
      // El horario pudo haberse ocupado mientras elegía: volvemos a los horarios.
      setError(err instanceof ApiError ? err.message : 'No pudimos reservar el turno.');
      setSlot(null);
      setPaso(2);
      disponibilidad.refetch();
    },
  });

  const elegirServicio = (elegido: ServicioReservable) => {
    setServicio(elegido);
    setSlot(null);
    setFecha('');
    setError(null);
    setPaso(2);
  };

  const elegirFecha = (nueva: string) => {
    setFecha(nueva);
    setSlot(null);
  };

  const volver = () => {
    setError(null);
    if (paso === 3) return setPaso(2);
    if (paso === 2) {
      setServicio(null);
      setSlot(null);
      return setPaso(1);
    }
  };

  const reiniciar = () => {
    setReservado(null);
    setServicio(null);
    setSlot(null);
    setNotas('');
    setError(null);
    setFecha('');
    setPaso(1);
  };

  if (reservado) {
    return <TurnoReservado turno={reservado} onReservarOtro={reiniciar} />;
  }

  const titulos: Record<Paso, string> = {
    1: 'Elegí tu tratamiento',
    2: 'Elegí día y horario',
    3: 'Confirmá tu turno',
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <View style={styles.header}>
          <View style={styles.headerFila}>
            {paso > 1 ? (
              <Pressable onPress={volver} hitSlop={12} accessibilityRole="button">
                <Feather name="chevron-left" size={22} color={colors.ink} />
              </Pressable>
            ) : null}
            <View style={styles.flex}>
              <AppText variant="label">
                {centroNombre ? `${centroNombre} · ` : ''}Paso {paso} de 3
              </AppText>
              <AppText variant="title" style={styles.titulo}>
                {titulos[paso]}
              </AppText>
            </View>
          </View>
          <View style={styles.progreso}>
            {([1, 2, 3] as Paso[]).map((n) => (
              <View key={n} style={[styles.segmento, n <= paso && styles.segmentoActivo]} />
            ))}
          </View>
        </View>

        <ScrollView
          contentContainerStyle={styles.content}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled">
          {error ? (
            <View style={styles.banner}>
              <Feather name="alert-circle" size={14} color={colors.danger} />
              <AppText variant="meta" color={colors.danger} style={styles.bannerTxt}>
                {error}
              </AppText>
            </View>
          ) : null}

          {paso === 1 ? (
            <PasoServicios
              cargando={serviciosQuery.isPending}
              error={serviciosQuery.isError}
              servicios={serviciosQuery.data?.results ?? []}
              onElegir={elegirServicio}
              onReintentar={serviciosQuery.refetch}
            />
          ) : null}

          {paso === 2 && servicio ? (
            <View style={styles.bloques}>
              <ResumenServicio servicio={servicio} />
              <View style={styles.bloque}>
                <View style={styles.bloqueHead}>
                  <AppText variant="section">Día</AppText>
                  <AppText variant="meta">{formatDiasReserva(servicio.dias_reserva)}</AppText>
                </View>
                <DateStrip dias={dias} seleccionada={fecha} onSeleccionar={elegirFecha} />
              </View>
              <View style={styles.bloque}>
                <AppText variant="section">Horario</AppText>
                <Horarios
                  cargando={disponibilidad.isPending || disponibilidad.isFetching}
                  error={disponibilidad.isError}
                  slots={disponibilidad.data?.slots ?? []}
                  motivo={disponibilidad.data?.motivo}
                  seleccionado={slot?.inicio ?? null}
                  onSeleccionar={setSlot}
                  onReintentar={disponibilidad.refetch}
                />
              </View>
            </View>
          ) : null}

          {paso === 3 && servicio && slot ? (
            <View style={styles.bloques}>
              <Card style={styles.resumen}>
                <AppText variant="label">Tu turno</AppText>
                <AppText variant="cardTitle" style={styles.resumenTitulo}>
                  {servicio.nombre}
                </AppText>
                <Dato icon="calendar" texto={formatFechaLarga(slot.inicio)} />
                <Dato
                  icon="clock"
                  texto={`${slot.hora} hs · ${servicio.duracion_minutos} min`}
                />
                {slot.profesional_nombre ? (
                  <Dato icon="user" texto={slot.profesional_nombre} />
                ) : null}
                <Dato icon="map-pin" texto={servicio.sucursal_nombre} />
                <View style={styles.total}>
                  <AppText variant="meta">Total</AppText>
                  <AppText variant="price">{formatPrecio(servicio.precio)}</AppText>
                </View>
              </Card>

              <Field
                label="Comentario (opcional)"
                placeholder="¿Algo que quieras contarnos?"
                value={notas}
                onChangeText={setNotas}
                multiline
                numberOfLines={3}
                maxLength={500}
                style={styles.notas}
              />

              <AppText variant="meta" style={styles.aviso}>
                Tu turno queda a confirmar por el centro. Vas a verlo en la pestaña Turnos.
              </AppText>
            </View>
          ) : null}
        </ScrollView>

        {paso === 2 ? (
          <Footer>
            <Button
              label="Continuar"
              disabled={!slot}
              onPress={() => {
                setError(null);
                setPaso(3);
              }}
            />
          </Footer>
        ) : null}

        {paso === 3 ? (
          <Footer>
            <Button
              label="Confirmar turno"
              loading={reserva.isPending}
              onPress={() => reserva.mutate()}
            />
          </Footer>
        ) : null}
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

function PasoServicios({
  cargando,
  error,
  servicios,
  onElegir,
  onReintentar,
}: {
  cargando: boolean;
  error: boolean;
  servicios: ServicioReservable[];
  onElegir: (servicio: ServicioReservable) => void;
  onReintentar: () => void;
}) {
  if (cargando) {
    return <ActivityIndicator color={colors.muted} style={styles.loader} />;
  }
  if (error) {
    return (
      <Pressable onPress={onReintentar} hitSlop={8}>
        <AppText variant="meta">
          No pudimos cargar los tratamientos. Tocá para reintentar.
        </AppText>
      </Pressable>
    );
  }
  if (servicios.length === 0) {
    return (
      <View style={styles.vacioServicios}>
        <Feather name="calendar" size={24} color={colors.taupe} />
        <AppText variant="cardTitle" style={styles.vacioTitulo}>
          Reservá con el centro
        </AppText>
        <AppText variant="meta" style={styles.vacioTxt}>
          Por ahora los turnos de este centro se coordinan directamente. Escribiles y con
          gusto te agendan.
        </AppText>
      </View>
    );
  }

  return (
    <View style={styles.lista}>
      {servicios.map((servicio) => (
        <Pressable
          key={servicio.id}
          onPress={() => onElegir(servicio)}
          accessibilityRole="button"
          style={({ pressed }) => [styles.servicioRow, pressed && styles.filaPresionada]}>
          <View style={styles.flex}>
            <AppText variant="cardTitle" style={styles.servicioNombre}>
              {servicio.nombre}
            </AppText>
            <AppText variant="meta">
              {servicio.duracion_minutos} min
              {servicio.categoria_nombre ? ` · ${servicio.categoria_nombre}` : ''}
            </AppText>
          </View>
          <AppText variant="price">{formatPrecio(servicio.precio)}</AppText>
          <Feather name="chevron-right" size={18} color={colors.muted} />
        </Pressable>
      ))}
    </View>
  );
}

function Horarios({
  cargando,
  error,
  slots,
  motivo,
  seleccionado,
  onSeleccionar,
  onReintentar,
}: {
  cargando: boolean;
  error: boolean;
  slots: SlotDisponible[];
  motivo?: string;
  seleccionado: string | null;
  onSeleccionar: (slot: SlotDisponible) => void;
  onReintentar: () => void;
}) {
  if (cargando) {
    return <ActivityIndicator color={colors.muted} style={styles.loader} />;
  }
  if (error) {
    return (
      <Pressable onPress={onReintentar} hitSlop={8}>
        <AppText variant="meta">No pudimos cargar los horarios. Tocá para reintentar.</AppText>
      </Pressable>
    );
  }
  if (slots.length === 0) {
    return (
      <AppText variant="meta" style={styles.sinSlots}>
        {motivo ?? 'No hay horarios disponibles este día. Probá con otra fecha.'}
      </AppText>
    );
  }
  return <SlotGrid slots={slots} seleccionado={seleccionado} onSeleccionar={onSeleccionar} />;
}

function ResumenServicio({ servicio }: { servicio: ServicioReservable }) {
  return (
    <View style={styles.chipServicio}>
      <Feather name="droplet" size={14} color={colors.ink} />
      <AppText variant="body" style={styles.flex} numberOfLines={1}>
        {servicio.nombre}
      </AppText>
      <AppText variant="meta">{servicio.duracion_minutos} min</AppText>
    </View>
  );
}

function Dato({ icon, texto }: { icon: 'calendar' | 'clock' | 'user' | 'map-pin'; texto: string }) {
  return (
    <View style={styles.dato}>
      <Feather name={icon} size={13} color={colors.muted} />
      <AppText variant="body">{texto}</AppText>
    </View>
  );
}

function Footer({ children }: { children: React.ReactNode }) {
  return <View style={styles.footer}>{children}</View>;
}

function TurnoReservado({
  turno,
  onReservarOtro,
}: {
  turno: TurnoApp;
  onReservarOtro: () => void;
}) {
  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.exito}>
        <View style={styles.check}>
          <Feather name="check" size={26} color={colors.ink} />
        </View>
        <AppText variant="title" style={styles.exitoTitulo}>
          Turno reservado
        </AppText>
        <AppText variant="meta" style={styles.exitoTxt}>
          Te esperamos. El centro va a confirmarlo a la brevedad.
        </AppText>

        <Card style={styles.exitoCard}>
          <AppText variant="cardTitle">{turno.servicio_nombre}</AppText>
          <Dato icon="calendar" texto={formatFechaLarga(turno.fecha_hora_inicio)} />
          <Dato icon="map-pin" texto={turno.sucursal_nombre} />
        </Card>

        <View style={styles.exitoAcciones}>
          <Button label="Ver mis turnos" onPress={() => router.push('/turnos')} />
          <Button label="Reservar otro" variant="ghost" onPress={onReservarOtro} />
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.ivory },
  flex: { flex: 1 },
  header: { paddingHorizontal: spacing.xl, paddingTop: spacing.sm, paddingBottom: 14, gap: 14 },
  headerFila: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  titulo: { marginTop: 4, fontSize: 26 },
  progreso: { flexDirection: 'row', gap: 5 },
  segmento: { flex: 1, height: 2, borderRadius: radius.pill, backgroundColor: colors.line },
  segmentoActivo: { backgroundColor: colors.ink },

  content: { paddingHorizontal: spacing.xl, paddingBottom: spacing.xxl, gap: spacing.lg },
  bloques: { gap: spacing.xl },
  bloque: { gap: spacing.md },
  bloqueHead: { flexDirection: 'row', alignItems: 'baseline', justifyContent: 'space-between' },
  vacioServicios: { alignItems: 'center', gap: spacing.sm, paddingVertical: spacing.xxl },
  vacioTitulo: { marginTop: spacing.sm },
  vacioTxt: { textAlign: 'center', lineHeight: 17 },
  lista: { gap: spacing.md },
  loader: { alignSelf: 'flex-start', marginTop: spacing.sm },

  banner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: 'rgba(169,82,76,0.08)',
    borderRadius: radius.md,
    padding: spacing.md,
  },
  bannerTxt: { flex: 1, lineHeight: 16 },

  servicioRow: {
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
  filaPresionada: { backgroundColor: colors.cream },
  servicioNombre: { fontSize: 16, lineHeight: 19 },

  chipServicio: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: colors.cream,
    borderRadius: radius.md,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
  },
  sinSlots: { lineHeight: 17 },

  resumen: { gap: 7 },
  resumenTitulo: { marginBottom: 5 },
  dato: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  total: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: spacing.md,
    paddingTop: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.line,
  },
  notas: { minHeight: 78, textAlignVertical: 'top' },
  aviso: { lineHeight: 17 },

  footer: {
    paddingHorizontal: spacing.xl,
    paddingTop: spacing.md,
    paddingBottom: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.line,
    backgroundColor: colors.ivory,
  },

  exito: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing.xl, gap: spacing.sm },
  check: {
    width: 58,
    height: 58,
    borderRadius: radius.pill,
    backgroundColor: colors.blush,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.sm,
  },
  exitoTitulo: { marginTop: spacing.sm },
  exitoTxt: { textAlign: 'center', lineHeight: 17 },
  exitoCard: { alignSelf: 'stretch', gap: 7, marginTop: spacing.lg },
  exitoAcciones: { alignSelf: 'stretch', gap: spacing.md, marginTop: spacing.xl },
});
