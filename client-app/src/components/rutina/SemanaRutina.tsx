import { StyleSheet, View } from 'react-native';

import { AppText } from '@/components/ui/AppText';
import { colors, fonts, radius } from '@/theme/ame';
import type { RutinaHoy } from '@/types/api';
import { DIAS_CORTOS, partesDeFecha } from '@/utils/rutina';

interface Props {
  hoy: RutinaHoy;
  /** `puntos`: fila chica de la tarjeta del inicio. `dias`: con el número del día. */
  variante: 'puntos' | 'dias';
}

/** La semana de lunes a domingo: lleno el día cumplido, con anillo el de hoy. */
export function SemanaRutina({ hoy, variante }: Props) {
  return (
    <View style={variante === 'puntos' ? styles.filaPuntos : styles.filaDias}>
      {hoy.semana.map((d, i) => {
        const esHoy = d.fecha === hoy.fecha;
        const etiqueta = DIAS_CORTOS[i];

        if (variante === 'puntos') {
          return (
            <View key={d.fecha} style={styles.colPuntos}>
              <View style={[styles.anilloPunto, esHoy && styles.anilloVisible]}>
                <View style={[styles.punto, d.cumplido && styles.lleno]} />
              </View>
              <AppText style={[styles.letraChica, esHoy && styles.letraHoy]}>{etiqueta}</AppText>
            </View>
          );
        }

        return (
          <View
            key={d.fecha}
            style={styles.colDias}
            accessible
            accessibilityLabel={`${etiqueta}${esHoy ? ', hoy' : ''}: ${d.cumplido ? 'rutina hecha' : 'sin rutina'}`}>
            <AppText style={[styles.letra, esHoy && styles.letraHoy]}>{etiqueta}</AppText>
            <View style={[styles.anilloDia, esHoy && styles.anilloVisible]}>
              <View style={[styles.dia, d.cumplido && styles.lleno]}>
                <AppText style={[styles.num, d.cumplido && styles.numLleno]}>
                  {partesDeFecha(d.fecha).dia}
                </AppText>
              </View>
            </View>
          </View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  filaPuntos: { flexDirection: 'row', gap: 9 },
  colPuntos: { alignItems: 'center', gap: 4 },
  anilloPunto: {
    padding: 2,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  anilloVisible: { borderColor: colors.ink },
  punto: {
    width: 8,
    height: 8,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: 'rgba(26,23,18,0.25)',
  },
  lleno: { backgroundColor: colors.ink, borderColor: colors.ink },
  letraChica: { fontFamily: fonts.sans, fontSize: 9, color: colors.rose },
  letraHoy: { fontFamily: fonts.sansMedium, color: colors.ink },

  filaDias: { flexDirection: 'row', justifyContent: 'space-between' },
  colDias: { alignItems: 'center', gap: 6, flex: 1 },
  letra: { fontFamily: fonts.sans, fontSize: 9.5, color: colors.muted },
  anilloDia: {
    padding: 2,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  dia: {
    width: 30,
    height: 30,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: colors.line,
    alignItems: 'center',
    justifyContent: 'center',
  },
  num: { fontFamily: fonts.sans, fontSize: 11.5, color: colors.muted },
  numLleno: { color: colors.onDark },
});
