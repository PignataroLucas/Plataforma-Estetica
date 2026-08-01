import { Feather } from '@expo/vector-icons';
import { useMemo, useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

import { AppText } from '@/components/ui/AppText';
import { colors, fonts, radius, spacing } from '@/theme/ame';
import { fechaISOLocal, formatMesAnio } from '@/utils/format';

/**
 * Calendario mensual para tratamientos con fechas puntuales.
 *
 * Cuando la máquina viene un viernes suelto, una tira de días no se entiende: hace
 * falta ver el mes para ubicar "el viernes 20". Solo se navega entre los meses que
 * tienen fechas disponibles — no tiene sentido pasear por meses vacíos.
 *
 * Ojo: al cambiar de tratamiento hay que remontarlo (`key={servicio.id}`), así el
 * mes visible vuelve al primero disponible del nuevo servicio.
 */

interface Props {
  /** Fechas reservables, ya filtradas por el backend. */
  fechas: Date[];
  /** Fecha elegida en formato YYYY-MM-DD. */
  seleccionada: string;
  onSeleccionar: (fecha: string) => void;
}

/** La semana arranca en lunes. */
const CABECERA = ['L', 'M', 'M', 'J', 'V', 'S', 'D'];

export function MonthCalendar({ fechas, seleccionada, onSeleccionar }: Props) {
  const meses = useMemo(() => agruparPorMes(fechas), [fechas]);
  const [indice, setIndice] = useState(0);

  if (meses.length === 0) return null;

  // El índice puede quedar fuera de rango si cambian las fechas (ej: refetch).
  const actual = meses[Math.min(indice, meses.length - 1)];
  const disponibles = new Set(actual.dias.map(fechaISOLocal));

  return (
    <View style={styles.calendario}>
      <View style={styles.cabecera}>
        <Flecha
          icono="chevron-left"
          etiqueta="Mes anterior"
          activa={indice > 0}
          onPress={() => setIndice(indice - 1)}
        />
        <AppText variant="cardTitle">{formatMesAnio(actual.primerDia)}</AppText>
        <Flecha
          icono="chevron-right"
          etiqueta="Mes siguiente"
          activa={indice < meses.length - 1}
          onPress={() => setIndice(indice + 1)}
        />
      </View>

      <View style={styles.fila}>
        {CABECERA.map((letra, i) => (
          <View key={i} style={styles.celda}>
            <AppText variant="label" color={colors.muted}>
              {letra}
            </AppText>
          </View>
        ))}
      </View>

      {semanasDelMes(actual.primerDia).map((semana, i) => (
        <View key={i} style={styles.fila}>
          {semana.map((dia, j) => {
            if (!dia) return <View key={`hueco-${j}`} style={styles.celda} />;

            const iso = fechaISOLocal(dia);
            const libre = disponibles.has(iso);
            const activa = iso === seleccionada;

            return (
              <View key={iso} style={styles.celda}>
                <Pressable
                  disabled={!libre}
                  onPress={() => onSeleccionar(iso)}
                  accessibilityRole="button"
                  accessibilityLabel={`${dia.getDate()} de ${formatMesAnio(dia)}`}
                  accessibilityState={{ selected: activa, disabled: !libre }}
                  style={({ pressed }) => [
                    styles.dia,
                    libre && styles.diaLibre,
                    activa && styles.diaActivo,
                    pressed && libre && !activa && styles.diaPresionado,
                  ]}>
                  <AppText
                    style={[
                      styles.numero,
                      !libre && styles.numeroApagado,
                      activa && styles.numeroActivo,
                    ]}>
                    {dia.getDate()}
                  </AppText>
                </Pressable>
              </View>
            );
          })}
        </View>
      ))}
    </View>
  );
}

function Flecha({
  icono,
  etiqueta,
  activa,
  onPress,
}: {
  icono: 'chevron-left' | 'chevron-right';
  etiqueta: string;
  activa: boolean;
  onPress: () => void;
}) {
  return (
    <Pressable
      onPress={onPress}
      disabled={!activa}
      hitSlop={10}
      accessibilityRole="button"
      accessibilityLabel={etiqueta}
      style={styles.flecha}>
      <Feather name={icono} size={18} color={activa ? colors.ink : colors.taupe} />
    </Pressable>
  );
}

interface Mes {
  /** Día 1 del mes, para el encabezado y para armar la grilla. */
  primerDia: Date;
  dias: Date[];
}

/** Agrupa las fechas disponibles por mes, en orden cronológico. */
function agruparPorMes(fechas: Date[]): Mes[] {
  const meses = new Map<string, Mes>();

  for (const fecha of [...fechas].sort((a, b) => a.getTime() - b.getTime())) {
    const clave = `${fecha.getFullYear()}-${fecha.getMonth()}`;
    const mes = meses.get(clave);
    if (mes) {
      mes.dias.push(fecha);
    } else {
      meses.set(clave, {
        primerDia: new Date(fecha.getFullYear(), fecha.getMonth(), 1),
        dias: [fecha],
      });
    }
  }

  return [...meses.values()];
}

/**
 * Días del mes repartidos en semanas de 7, arrancando en lunes.
 * Los `null` son los huecos antes del día 1 y después del último.
 */
function semanasDelMes(primerDia: Date): (Date | null)[][] {
  const anio = primerDia.getFullYear();
  const mes = primerDia.getMonth();
  // getDay(): 0 = domingo. Con la semana arrancando en lunes, el domingo va al final.
  const offset = (primerDia.getDay() + 6) % 7;
  const totalDias = new Date(anio, mes + 1, 0).getDate();

  const celdas: (Date | null)[] = Array<null>(offset).fill(null);
  for (let d = 1; d <= totalDias; d += 1) celdas.push(new Date(anio, mes, d));
  while (celdas.length % 7 !== 0) celdas.push(null);

  const semanas: (Date | null)[][] = [];
  for (let i = 0; i < celdas.length; i += 7) semanas.push(celdas.slice(i, i + 7));
  return semanas;
}

const styles = StyleSheet.create({
  calendario: {
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    padding: spacing.md,
    gap: 2,
  },
  cabecera: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.xs,
    paddingBottom: spacing.sm,
  },
  flecha: { width: 32, height: 32, alignItems: 'center', justifyContent: 'center' },

  fila: { flexDirection: 'row' },
  celda: { flex: 1, alignItems: 'center', paddingVertical: 2 },
  dia: {
    width: 36,
    height: 36,
    borderRadius: radius.sm,
    alignItems: 'center',
    justifyContent: 'center',
  },
  // Solo los días reservables se ven "tocables"; el resto queda de fondo.
  diaLibre: { backgroundColor: colors.cream },
  diaPresionado: { backgroundColor: colors.blush },
  diaActivo: { backgroundColor: colors.ink },
  numero: { fontFamily: fonts.serif, fontSize: 17, lineHeight: 21, color: colors.ink },
  numeroApagado: { color: colors.taupe },
  numeroActivo: { color: colors.onDark },
});
