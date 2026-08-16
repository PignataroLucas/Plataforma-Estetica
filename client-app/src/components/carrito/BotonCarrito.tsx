import { Feather } from '@expo/vector-icons';
import { router } from 'expo-router';
import { Pressable, StyleSheet, View } from 'react-native';

import { AppText } from '@/components/ui/AppText';
import { useUnidadesEnCarrito } from '@/stores/carrito';
import { colors, radius } from '@/theme/ame';

/**
 * Acceso al carrito con el contador de unidades. Va en el header de la Tienda
 * y de la ficha, que son las dos pantallas desde donde se agrega.
 *
 * Sin items no se dibuja: un carrito vacío en el header es ruido y además
 * insinúa que la clienta dejó algo adentro cuando no dejó nada.
 */
export function BotonCarrito() {
  const unidades = useUnidadesEnCarrito();
  if (unidades === 0) return null;

  return (
    <Pressable
      onPress={() => router.push('/carrito')}
      hitSlop={12}
      style={styles.boton}
      accessibilityRole="button"
      accessibilityLabel={`Ver carrito, ${unidades} ${unidades === 1 ? 'unidad' : 'unidades'}`}>
      <Feather name="shopping-bag" size={20} color={colors.ink} />
      <View style={styles.globo}>
        <AppText style={styles.numero}>{unidades > 99 ? '99+' : unidades}</AppText>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  boton: { width: 40, height: 40, alignItems: 'flex-end', justifyContent: 'center' },
  globo: {
    position: 'absolute',
    top: 2,
    right: -6,
    minWidth: 16,
    height: 16,
    paddingHorizontal: 4,
    borderRadius: radius.pill,
    backgroundColor: colors.ink,
    alignItems: 'center',
    justifyContent: 'center',
  },
  numero: { fontFamily: 'Inter_500Medium', fontSize: 9, color: colors.onDark },
});
