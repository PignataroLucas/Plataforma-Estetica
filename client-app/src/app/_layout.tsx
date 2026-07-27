import {
  CormorantGaramond_400Regular,
  CormorantGaramond_500Medium,
  CormorantGaramond_600SemiBold,
} from '@expo-google-fonts/cormorant-garamond';
import { Inter_300Light, Inter_400Regular, Inter_500Medium } from '@expo-google-fonts/inter';
import { QueryClientProvider } from '@tanstack/react-query';
import { Stack } from 'expo-router';
import { useFonts } from 'expo-font';
import * as SplashScreen from 'expo-splash-screen';
import { StatusBar } from 'expo-status-bar';
import { useEffect } from 'react';
import { Platform, View, StyleSheet } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';

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
  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Protected guard={authenticated}>
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="mi-rutina" options={{ animation: 'slide_from_right' }} />
      </Stack.Protected>
      <Stack.Protected guard={!authenticated}>
        <Stack.Screen name="(auth)" />
      </Stack.Protected>
    </Stack>
  );
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
