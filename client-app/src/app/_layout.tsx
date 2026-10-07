import {
  CormorantGaramond_400Regular,
  CormorantGaramond_500Medium,
  CormorantGaramond_600SemiBold,
} from '@expo-google-fonts/cormorant-garamond';
import { Inter_300Light, Inter_400Regular, Inter_500Medium } from '@expo-google-fonts/inter';
import { QueryClientProvider } from '@tanstack/react-query';
import { Stack, useSegments } from 'expo-router';
import { useFonts } from 'expo-font';
import * as SplashScreen from 'expo-splash-screen';
import { StatusBar } from 'expo-status-bar';
import { useEffect } from 'react';
import { Platform, View, StyleSheet } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { TransicionEntrada } from '@/components/TransicionEntrada';
import { usePushNotifications } from '@/hooks/usePushNotifications';
import { analytics } from '@/services/analytics';
import { queryClient } from '@/services/queryClient';
import { useAuthStore } from '@/stores/auth';
import { colors } from '@/theme/ame';

SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const [fontsLoaded] = useFonts({
    CormorantGaramond_400Regular,
    CormorantGaramond_500Medium,
    CormorantGaramond_600SemiBold,
    Inter_300Light,
    Inter_400Regular,
    Inter_500Medium,
  });

  const status = useAuthStore((s) => s.status);
  const hydrate = useAuthStore((s) => s.hydrate);

  // Al arrancar, cargamos la sesión persistida y validamos el token.
  useEffect(() => {
    hydrate();
  }, [hydrate]);

  const ready = fontsLoaded && status !== 'loading';

  useEffect(() => {
    if (ready) SplashScreen.hideAsync();
  }, [ready]);

  // Mantenemos el splash hasta tener fuentes + estado de sesión resuelto.
  if (!ready) return null;

  return (
    <QueryClientProvider client={queryClient}>
      <SafeAreaProvider>
        <StatusBar style="dark" />
        <View style={styles.page}>
          <View style={styles.shell}>
            <RootNavigator authenticated={status === 'authenticated'} />
            {/* Va acá, último y dentro del shell, para quedar por encima de las
                tabs y tapar el montaje de Inicio. */}
            <TransicionEntrada />
          </View>
        </View>
      </SafeAreaProvider>
    </QueryClientProvider>
  );
}

/**
 * Gate de navegación. `Stack.Protected` deja accesible solo el grupo cuyo guard
 * es true; al cambiar de sesión, expo-router redirige automáticamente al grupo
 * disponible (tabs si hay sesión, bienvenida/auth si no).
 */
function RootNavigator({ authenticated }: { authenticated: boolean }) {
  // Va acá y no en RootLayout porque necesita el QueryClientProvider ya montado,
  // y porque para navegar el Stack tiene que existir.
  usePushNotifications();
  usePantallaMedida();

  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Protected guard={authenticated}>
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="mi-rutina" options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="servicios" options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="servicio/[id]" options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="carrito" options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="checkout" options={{ animation: 'slide_from_bottom' }} />
        <Stack.Screen name="eliminar-cuenta" options={{ animation: 'slide_from_right' }} />
      </Stack.Protected>
      <Stack.Protected guard={!authenticated}>
        <Stack.Screen name="(auth)" />
      </Stack.Protected>
    </Stack>
  );
}

/**
 * Manda a Analytics cada pantalla que se ve.
 *
 * Con los segmentos y no con `usePathname`: el pathname trae el id real
 * (`/producto/12`) y cada producto contaría como una pantalla distinta. Los
 * segmentos traen la forma del archivo (`/producto/[id]`). Los grupos entre
 * paréntesis se sacan porque no son parte de la URL.
 */
function usePantallaMedida() {
  const segmentos = useSegments();
  const ruta =
    '/' + segmentos.filter((s) => !(s.startsWith('(') && s.endsWith(')'))).join('/');

  useEffect(() => {
    analytics.pantalla(ruta);
  }, [ruta]);
}

const styles = StyleSheet.create({
  // En web centramos la app en una columna de ancho teléfono; en nativo ocupa todo.
  page: {
    flex: 1,
    backgroundColor: Platform.OS === 'web' ? '#DED2C6' : colors.ivory,
    alignItems: 'center',
  },
  shell: {
    flex: 1,
    width: '100%',
    maxWidth: Platform.OS === 'web' ? 440 : undefined,
    backgroundColor: colors.ivory,
  },
});
