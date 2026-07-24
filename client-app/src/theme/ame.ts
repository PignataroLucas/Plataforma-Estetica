/**
 * Sistema de diseño AME — derivado del manual de marca.
 * Paleta, tipografía, espaciado y radios. Fuente única de verdad para toda la UI.
 */

export const colors = {
  ivory: '#F5F0EA', // fondo principal
  cream: '#EBE0CE', // superficies / categorías
  blush: '#E8D1CD', // acento
  taupe: '#D5C4B9', // bordes / secundarios
  ink: '#1A1712', // texto y CTAs (near-black cálido)
  muted: '#9C8E7F', // texto secundario
  line: 'rgba(26,23,18,0.09)', // divisores / bordes sutiles
  card: '#FCFAF6', // tarjetas claras
  onDark: '#EFE7DC', // texto sobre superficies oscuras (card negra / botones)
  onDarkMuted: 'rgba(239,231,220,0.6)',
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 28,
} as const;

export const radius = {
  sm: 11,
  md: 14,
  lg: 17,
  xl: 22,
  pill: 999,
} as const;

/** Nombres de familia exactos cargados con expo-google-fonts. */
export const fonts = {
  serif: 'CormorantGaramond_500Medium',
  serifRegular: 'CormorantGaramond_400Regular',
  serifSemi: 'CormorantGaramond_600SemiBold',
  sansLight: 'Inter_300Light',
  sans: 'Inter_400Regular',
  sansMedium: 'Inter_500Medium',
} as const;

export const theme = { colors, spacing, radius, fonts } as const;
export type AmeTheme = typeof theme;
