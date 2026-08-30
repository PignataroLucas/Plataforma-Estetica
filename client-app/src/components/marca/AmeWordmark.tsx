/**
 * El wordmark de AME dibujándose trazo a trazo.
 *
 * Dos etapas encadenadas, y la segunda es la que hace que no parezca un truco:
 * cada letra se traza siguiendo su contorno, escalonada (A, M, E), y cuando la
 * última termina el relleno entra con un fundido mientras el trazo se apaga, así
 * el logo **se asienta** en su forma sólida en vez de quedar dibujado en línea.
 *
 * Todo sale de **una sola línea de tiempo lineal** de la que cada parte toma su
 * ventana por interpolación. La primera versión encadenaba `withDelay` y un
 * callback con `runOnJS`, y el relleno se cancelaba a los dos frames: con un
 * único `withTiming` no hay nada que cancelar ni que sincronizar.
 *
 * El trazado va a velocidad constante a propósito —es una pluma avanzando— y el
 * suavizado se aplica solo al relleno, con un smoothstep hecho a mano para no
 * depender de las curvas de Reanimated dentro del worklet.
 *
 * Sobre el ritmo: es deliberadamente lento y sin rebote. Un `withSpring` con sus
 * valores por defecto sobrepasa y vuelve, y eso lee como app de tecnología; la
 * marca es un serif de alto contraste y pide lo contrario.
 *
 * Nota sobre el trazo: esto recorre el **contorno** de la letra, no su esqueleto.
 * No es escritura a mano —para eso haría falta un trazo de un solo recorrido,
 * dibujado por una diseñadora— sino algo más cercano a un grabado apareciendo.
 * En un serif de alto contraste funciona porque el contorno *es* el carácter.
 */
import { useEffect } from 'react';
import { AccessibilityInfo, View, type StyleProp, type ViewStyle } from 'react-native';
import Animated, {
  Easing,
  Extrapolation,
  interpolate,
  useAnimatedProps,
  useSharedValue,
  withTiming,
  type SharedValue,
} from 'react-native-reanimated';
import Svg, { Path } from 'react-native-svg';

import { colors } from '@/theme/ame';

import { WORDMARK_ALTO, WORDMARK_ANCHO, WORDMARK_LETRAS } from './wordmarkPaths';

const PathAnimado = Animated.createAnimatedComponent(Path);

/** Cuánto tarda cada letra en trazarse, y cuánto espera la siguiente. */
const DURACION_LETRA = 450;
const ESCALONADO = 260;
/** El fundido del relleno, una vez dibujada la última letra. */
const DURACION_RELLENO = 520;

const FIN_DEL_TRAZO = ESCALONADO * (WORDMARK_LETRAS.length - 1) + DURACION_LETRA;

/** Lo que tarda la animación completa. La usa quien encadene algo después. */
export const DURACION_WORDMARK = FIN_DEL_TRAZO + DURACION_RELLENO;

/** Fracción de la línea de tiempo en la que arranca el relleno. */
const INICIO_RELLENO = FIN_DEL_TRAZO / DURACION_WORDMARK;

interface Props {
  /**
   * Línea de tiempo externa, 0 → 1, si esta animación es parte de una secuencia
   * mayor. Sin ella el componente corre la suya al montarse.
   */
  progreso?: SharedValue<number>;
  /** Ancho en puntos. El alto sale de la proporción del wordmark. */
  ancho?: number;
  /** Grosor del trazo mientras se dibuja, en unidades del viewBox. */
  grosor?: number;
  color?: string;
  style?: StyleProp<ViewStyle>;
}

export function AmeWordmark({
  progreso,
  ancho = 220,
  grosor = 5,
  color = colors.ink,
  style,
}: Props) {
  const propio = useSharedValue(0);
  const linea = progreso ?? propio;

  useEffect(() => {
    // Si la línea de tiempo la maneja otro, acá no hay nada que arrancar.
    if (progreso) return;

    let vigente = true;
    AccessibilityInfo.isReduceMotionEnabled().then((reducido) => {
      if (!vigente) return;
      // Quien pidió menos movimiento ve el logo ya asentado.
      propio.value = reducido
        ? 1
        : withTiming(1, { duration: DURACION_WORDMARK, easing: Easing.linear });
    });

    return () => {
      vigente = false;
    };
    // Animación de entrada: corre una sola vez.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const alto = (ancho * WORDMARK_ALTO) / WORDMARK_ANCHO;

  return (
    <View style={[{ width: ancho, height: alto }, style]} accessibilityLabel="AME">
      <Svg width={ancho} height={alto} viewBox={`0 0 ${WORDMARK_ANCHO} ${WORDMARK_ALTO}`}>
        {WORDMARK_LETRAS.map((letra, i) => (
          <Letra
            key={letra.letra}
            d={letra.d}
            largo={letra.largo}
            color={color}
            grosor={grosor}
            linea={linea}
            // Cada letra ocupa su ventana dentro del 0 → 1 global.
            desde={(ESCALONADO * i) / DURACION_WORDMARK}
            hasta={(ESCALONADO * i + DURACION_LETRA) / DURACION_WORDMARK}
          />
        ))}
      </Svg>
    </View>
  );
}

function Letra({
  d,
  largo,
  color,
  grosor,
  linea,
  desde,
  hasta,
}: {
  d: string;
  largo: number;
  color: string;
  grosor: number;
  linea: SharedValue<number>;
  desde: number;
  hasta: number;
}) {
  const props = useAnimatedProps(() => {
    const avance = interpolate(linea.value, [desde, hasta], [0, 1], Extrapolation.CLAMP);

    const crudo = interpolate(linea.value, [INICIO_RELLENO, 1], [0, 1], Extrapolation.CLAMP);
    // Smoothstep a mano: suaviza las dos puntas sin traer una curva de fuera.
    const relleno = crudo * crudo * (3 - 2 * crudo);

    return {
      // El dash mide todo el contorno: el offset lo va descubriendo.
      strokeDashoffset: largo * (1 - avance),
      // El relleno entra mientras el trazo se apaga. Los dos a la vez evitan el
      // parpadeo de ver la línea encima de la letra ya rellena.
      fillOpacity: relleno,
      strokeOpacity: 1 - relleno,
    };
  });

  return (
    <PathAnimado
      d={d}
      fill={color}
      stroke={color}
      strokeWidth={grosor}
      strokeDasharray={largo}
      animatedProps={props}
    />
  );
}
