/**
 * La pantalla que tapa el salto entre "puse mis datos" y la app.
 *
 * Resuelve dos cosas que son la misma: sin esto, al iniciar sesión el formulario
 * se cambia de golpe por un Inicio vacío con un spinner, porque recién ahí
 * empiezan a pedirse los datos. Acá se usa ese tiempo para **precargarlos**, así
 * que cuando la cortina se levanta el Inicio ya está completo.
 *
 * Espera dos cosas a la vez y se va con la última:
 *
 * - Que termine la animación del logo, para que no sea un parpadeo.
 * - Que los datos de Inicio estén en el cache.
 *
 * Y tiene un tope: si la red está lenta, a los `ESPERA_MAXIMA` se levanta igual y
 * deja que Inicio muestre su propio estado de carga. Una espera indefinida sobre
 * una pantalla sin botones sería una app colgada.
 *
 * Las claves de query son **exactamente** las de `(tabs)/index.tsx`. Si allá
 * cambian y acá no, esto sigue "funcionando" pero deja de precargar nada, que es
 * la clase de defecto que no se nota: la pantalla se ve igual, el Inicio vuelve
 * a tardar. Los tipos no lo atajan.
 */
import { useEffect, useState } from 'react';
import { StyleSheet, View } from 'react-native';
import Animated, {
  Easing,
  useAnimatedStyle,
  useSharedValue,
  withTiming,
} from 'react-native-reanimated';

import { AmeWordmark, DURACION_WORDMARK } from '@/components/marca/AmeWordmark';
import { useCentroActivo } from '@/hooks/useCentroActivo';
import { getServicios } from '@/services/public';
import { queryClient } from '@/services/queryClient';
import { getMiRutina } from '@/services/rutina';
import { getMisTurnos } from '@/services/turnos';
import { useAuthStore } from '@/stores/auth';
import { colors } from '@/theme/ame';

/** Un respiro después del logo, para que no se corte encima del último frame. */
const RESPIRO = 220;
/** Cuánto dura el fundido de salida. */
const SALIDA = 420;
/** Tope duro: pasado esto se levanta aunque los datos no hayan llegado. */
const ESPERA_MAXIMA = 6000;

export function TransicionEntrada() {
  const entrando = useAuthStore((s) => s.entrando);
  if (!entrando) return null;
  return <Cortina />;
}

/**
 * En un componente aparte para que los hooks —y con ellos la precarga y los
 * temporizadores— arranquen al montarse y no en cada login sobre el mismo árbol.
 */
function Cortina() {
  const { centroId } = useCentroActivo();
  const terminarEntrada = useAuthStore((s) => s.terminarEntrada);
  const [listo, setListo] = useState(false);
  const salida = useSharedValue(0);

  // --- Precarga + espera mínima ---
  useEffect(() => {
    let vigente = true;

    const minimo = new Promise((r) => setTimeout(r, DURACION_WORDMARK + RESPIRO));

    // `allSettled`: que falle una no puede dejar la cortina puesta. Si alguna se
    // cae, Inicio la vuelve a pedir y muestra su propio error.
    const datos = Promise.allSettled([
      queryClient.prefetchQuery({
        queryKey: ['servicios', centroId],
        queryFn: () => getServicios(centroId),
      }),
      queryClient.prefetchQuery({ queryKey: ['mi-rutina'], queryFn: () => getMiRutina() }),
      queryClient.prefetchQuery({ queryKey: ['mis-turnos'], queryFn: () => getMisTurnos() }),
    ]);

    const tope = new Promise((r) => setTimeout(r, ESPERA_MAXIMA));

    Promise.race([Promise.all([minimo, datos]), tope]).then(() => {
      if (vigente) setListo(true);
    });

    return () => {
      vigente = false;
    };
  }, [centroId]);

  // --- Salida ---
  useEffect(() => {
    if (!listo) return;

    salida.value = withTiming(1, { duration: SALIDA, easing: Easing.out(Easing.cubic) });
    // El desmontaje va por temporizador y no por el callback de `withTiming`:
    // encadenar `runOnJS` dentro del worklet fue lo que rompió la primera versión
    // de la animación de bienvenida.
    const t = setTimeout(terminarEntrada, SALIDA);
    return () => clearTimeout(t);
  }, [listo, salida, terminarEntrada]);

  const estilo = useAnimatedStyle(() => ({ opacity: 1 - salida.value }));

  return (
    <Animated.View style={[styles.cortina, estilo]} pointerEvents="auto">
      <View style={styles.centro}>
        <AmeWordmark ancho={200} />
      </View>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  cortina: {
    position: 'absolute',
    top: 0,
    right: 0,
    bottom: 0,
    left: 0,
    backgroundColor: colors.ivory,
    // Por encima de las tabs y de cualquier pantalla que se esté montando detrás.
    zIndex: 10,
  },
  centro: { flex: 1, alignItems: 'center', justifyContent: 'center' },
});
