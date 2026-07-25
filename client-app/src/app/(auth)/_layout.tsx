import { Stack } from 'expo-router';

import { colors } from '@/theme/ame';

// Ruta ancla del grupo: al entrar sin sesión, se aterriza en Bienvenida.
export const unstable_settings = {
  initialRouteName: 'bienvenida',
};

export default function AuthLayout() {
  return (
    <Stack
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: colors.ivory },
        animation: 'slide_from_right',
      }}
    />
  );
}
