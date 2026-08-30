/**
 * Un `Pressable` que responde al tacto: se hunde apenas y se aclara.
 *
 * Existe para que el gesto se sienta **igual en toda la app**. Si cada tarjeta
 * animara distinto, el conjunto leería como descuidado, que es justo lo que se
 * quiere evitar en una app de belleza.
 *
 * El ritmo es asimétrico a propósito: entra rápido (90 ms) y suelta lento
 * (260 ms). Así el hundimiento se siente inmediato —el dedo todavía está sobre
 * la pantalla— y la vuelta queda suave en vez de rebotar.
 *
 * **No va en todo lo tocable.** Un link de texto que se achica queda raro; para
 * eso está `escala={1}`, que deja solo el aclarado. La regla práctica: lo que
 * tiene superficie propia (botones, tarjetas, celdas) se hunde; lo que es texto
 * suelto, no.
 */
import { forwardRef } from 'react';
import { Pressable, type PressableProps, type StyleProp, type ViewStyle, type View } from 'react-native';
import Animated, {
  Easing,
  useAnimatedStyle,
  useSharedValue,
  withTiming,
} from 'react-native-reanimated';

const PressableAnimado = Animated.createAnimatedComponent(Pressable);

/** Entra rápido, suelta lento. */
const AL_HUNDIR = 90;
const AL_SOLTAR = 260;

export interface PresionableProps extends Omit<PressableProps, 'style'> {
  /**
   * Cuánto se hunde. 0.97 es el valor de la casa; `1` desactiva el hundimiento
   * y deja solo la opacidad, para texto suelto.
   */
  escala?: number;
  /** Cuánto se aclara al hundirse. */
  atenuacion?: number;
  style?: StyleProp<ViewStyle>;
}

export const Presionable = forwardRef<View, PresionableProps>(function Presionable(
  { escala = 0.97, atenuacion = 0.12, style, disabled, onPressIn, onPressOut, ...rest },
  ref,
) {
  const hundido = useSharedValue(0);

  const animado = useAnimatedStyle(() => ({
    transform: [{ scale: 1 - hundido.value * (1 - escala) }],
    opacity: 1 - hundido.value * atenuacion,
  }));

  return (
    <PressableAnimado
      ref={ref}
      disabled={disabled}
      onPressIn={(e) => {
        // Lo deshabilitado no responde al tacto: prometer un gesto que no va a
        // pasar nada es peor que no responder.
        if (!disabled) hundido.value = withTiming(1, { duration: AL_HUNDIR });
        onPressIn?.(e);
      }}
      onPressOut={(e) => {
        hundido.value = withTiming(0, {
          duration: AL_SOLTAR,
          easing: Easing.out(Easing.cubic),
        });
        onPressOut?.(e);
      }}
      style={[style, animado]}
      {...rest}
    />
  );
});
