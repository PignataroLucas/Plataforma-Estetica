// `Tabs` desde 'expo-router' está deprecado por el propio paquete a favor de
// este subpath, que además es de donde AmeTabBar toma sus tipos.
import { Tabs } from 'expo-router/js-tabs';

import { AmeTabBar } from '@/components/AmeTabBar';

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{ headerShown: false }}
      tabBar={(props) => <AmeTabBar {...props} />}>
      <Tabs.Screen name="index" />
      <Tabs.Screen name="turnos" />
      <Tabs.Screen name="reservar" />
      <Tabs.Screen name="promos" />
      <Tabs.Screen name="perfil" />
    </Tabs>
  );
}
