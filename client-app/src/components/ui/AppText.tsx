import { Text, TextProps, StyleSheet } from 'react-native';

import { colors, fonts } from '@/theme/ame';

type Variant =
  | 'display' // logo / hero serif
  | 'title' // nombre grande (ej: Valentina)
  | 'section' // título de sección (ej: Categorías)
  | 'cardTitle' // nombre en card (turno / tratamiento)
  | 'label' // etiqueta uppercase con tracking
  | 'body'
  | 'meta' // texto secundario chico
  | 'price'
  | 'button';

export interface AppTextProps extends TextProps {
  variant?: Variant;
  color?: string;
}

export function AppText({ variant = 'body', color, style, ...rest }: AppTextProps) {
  return <Text {...rest} style={[styles[variant], color ? { color } : null, style]} />;
}

const styles = StyleSheet.create({
  display: { fontFamily: fonts.serif, fontSize: 56, color: colors.ink, letterSpacing: 3 },
  title: { fontFamily: fonts.serif, fontSize: 29, color: colors.ink },
  section: { fontFamily: fonts.serif, fontSize: 21, color: colors.ink },
  cardTitle: { fontFamily: fonts.serif, fontSize: 19, color: colors.ink },
  label: {
    fontFamily: fonts.sansMedium,
    fontSize: 9.5,
    letterSpacing: 1.8,
    textTransform: 'uppercase',
    color: colors.muted,
  },
  body: { fontFamily: fonts.sans, fontSize: 14, color: colors.ink },
  meta: { fontFamily: fonts.sansLight, fontSize: 11, color: colors.muted },
  price: { fontFamily: fonts.sansMedium, fontSize: 13, color: colors.ink },
  button: { fontFamily: fonts.sansMedium, fontSize: 14, color: colors.onDark },
});
