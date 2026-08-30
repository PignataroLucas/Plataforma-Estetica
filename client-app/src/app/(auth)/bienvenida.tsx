import { router } from 'expo-router';
import { useEffect } from 'react';
import {
  AccessibilityInfo,
  Pressable,
  StyleSheet,
  View,
  type StyleProp,
  type ViewStyle,
} from 'react-native';
import Animated, {
  Easing,
  Extrapolation,
  interpolate,
  useAnimatedStyle,
  useSharedValue,
  withTiming,
  type SharedValue,
} from 'react-native-reanimated';
import { SafeAreaView } from 'react-native-safe-area-context';

import { AmeWordmark, DURACION_WORDMARK } from '@/components/marca/AmeWordmark';
import { AppText } from '@/components/ui/AppText';
import { Button } from '@/components/ui/Button';
import { colors, fonts, spacing } from '@/theme/ame';

/** Lo que tarda el resto del contenido en terminar de entrar, tras el logo. */
const DURACION_RESTO = 900;
const DURACION_INTRO = DURACION_WORDMARK + DURACION_RESTO;

/** Fracción de la intro en la que el logo ya se asentó y entra lo demás. */
const FIN_DEL_LOGO = DURACION_WORDMARK / DURACION_INTRO;

/**
 * Primera pantalla, y la única impresión que se da una sola vez.
 *
 * El logo se dibuja solo y, cuando termina de asentarse, entra el resto
 * escalonado. Una **sola** línea de tiempo gobierna las dos cosas: el logo toma
 * su tramo inicial y cada bloque de texto el suyo, más adelante. Encadenarlo con
 * un callback al terminar el logo fue la primera versión y era frágil.
 *
 * Todo el contenido está montado desde el principio y solo cambia su opacidad:
 * si apareciera recién al final, el `hero` centrado se reacomodaría y el logo
 * pegaría un salto justo en el momento de más atención.
 */
export default function Bienvenida() {
  // 0 → 1 recorre la intro entera: primero el logo, después el resto.
  const intro = useSharedValue(0);

  useEffect(() => {
    let vigente = true;
    AccessibilityInfo.isReduceMotionEnabled().then((reducido) => {
      if (!vigente) return;
      intro.value = reducido
        ? 1
        : withTiming(1, { duration: DURACION_INTRO, easing: Easing.linear });
    });
    return () => {
      vigente = false;
    };
    // Animación de entrada: corre una sola vez.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
      <View style={styles.hero}>
        <AppText variant="label" style={styles.kicker}>
          Bienvenida a
        </AppText>

        <AmeWordmark ancho={232} progreso={intro} />

        <Aparece progreso={intro} desde={FIN_DEL_LOGO}>
          <AppText style={styles.sub}>esencial</AppText>
        </Aparece>

        <Aparece progreso={intro} desde={FIN_DEL_LOGO + 0.07} style={styles.pitchCaja}>
          <AppText variant="body" color={colors.muted} style={styles.pitch}>
            Tu ritual de cuidado, tus turnos y tus beneficios, en un solo lugar.
          </AppText>
        </Aparece>
      </View>

      <Aparece progreso={intro} desde={FIN_DEL_LOGO + 0.14} style={styles.actions}>
        <Button label="Ingresar con mi código" onPress={() => router.push('/codigo')} />
        <Button
          label="Crear una cuenta"
          variant="ghost"
          onPress={() => router.push('/registro')}
        />
        <Pressable
          onPress={() => router.push('/login')}
          hitSlop={8}
          style={styles.loginLink}
          accessibilityRole="button">
          <AppText variant="meta">¿Ya tenés cuenta? </AppText>
          <AppText variant="meta" color={colors.ink} style={styles.loginStrong}>
            Iniciar sesión
          </AppText>
        </Pressable>
      </Aparece>
    </SafeAreaView>
  );
}

/**
 * Aparece con un fundido y 10 px de subida, tomando su turno de `progreso`.
 *
 * El desplazamiento es corto a propósito: lo suficiente para que se perciba
 * movimiento, no tanto como para que parezca que la pantalla se arma sola.
 */
function Aparece({
  progreso,
  desde,
  style,
  children,
}: {
  progreso: SharedValue<number>;
  desde: number;
  style?: StyleProp<ViewStyle>;
  children: React.ReactNode;
}) {
  const estilo = useAnimatedStyle(() => {
    const crudo = interpolate(progreso.value, [desde, desde + 0.2], [0, 1], Extrapolation.CLAMP);
    // Mismo smoothstep que el wordmark, para que todo tenga el mismo carácter.
    const p = crudo * crudo * (3 - 2 * crudo);
    return { opacity: p, transform: [{ translateY: (1 - p) * 10 }] };
  });

  return <Animated.View style={[style, estilo]}>{children}</Animated.View>;
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.ivory,
    paddingHorizontal: spacing.xl,
    paddingBottom: spacing.xl,
  },
  hero: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  kicker: { marginBottom: spacing.md },
  sub: {
    fontFamily: fonts.serifRegular,
    fontSize: 22,
    letterSpacing: 6,
    color: colors.muted,
    marginTop: 2,
    textAlign: 'center',
  },
  pitchCaja: { marginTop: spacing.xl, paddingHorizontal: spacing.md },
  pitch: { textAlign: 'center', lineHeight: 21 },
  actions: { gap: spacing.md },
  loginLink: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: spacing.sm,
    paddingVertical: spacing.sm,
  },
  loginStrong: { textDecorationLine: 'underline' },
});
