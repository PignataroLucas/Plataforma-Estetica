import { Tabs } from 'expo-router';

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
