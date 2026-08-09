import { Feather } from '@expo/vector-icons';
// expo-router vendoriza React Navigation: el tipo sale de acá y no del paquete
// `@react-navigation/bottom-tabs`, que este stack no tiene como dependencia.
import type { BottomTabBarProps } from 'expo-router/js-tabs';
import { View, Pressable, StyleSheet } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { AppText } from '@/components/ui/AppText';
import { colors, radius, spacing } from '@/theme/ame';

type FeatherName = keyof typeof Feather.glyphMap;

const TABS: Record<string, { label: string; icon: FeatherName; central?: boolean }> = {
  index: { label: 'Inicio', icon: 'home' },
  turnos: { label: 'Turnos', icon: 'calendar' },
  reservar: { label: 'Reservar', icon: 'plus', central: true },
  promos: { label: 'Promos', icon: 'star' },
  perfil: { label: 'Perfil', icon: 'user' },
};

export function AmeTabBar({ state, navigation }: BottomTabBarProps) {
  const insets = useSafeAreaInsets();

  return (
    <View style={[styles.bar, { paddingBottom: Math.max(insets.bottom, 12) }]}>
      {state.routes.map((route, index) => {
        const cfg = TABS[route.name];
        if (!cfg) return null;
        const focused = state.index === index;

        const onPress = () => {
          const event = navigation.emit({ type: 'tabPress', target: route.key, canPreventDefault: true });
          if (!focused && !event.defaultPrevented) navigation.navigate(route.name);
        };

        if (cfg.central) {
          return (
            <Pressable key={route.key} style={styles.centralItem} onPress={onPress}>
              <View style={styles.plus}>
                <Feather name={cfg.icon} size={20} color={colors.onDark} />
              </View>
              <AppText style={styles.centralLabel}>{cfg.label}</AppText>
            </Pressable>
          );
        }

        return (
          <Pressable key={route.key} style={styles.item} onPress={onPress}>
            <Feather name={cfg.icon} size={20} color={focused ? colors.ink : colors.muted} />
            <AppText style={[styles.label, { color: focused ? colors.ink : colors.muted }]}>
              {cfg.label}
            </AppText>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  bar: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'space-around',
    paddingTop: 9,
    paddingHorizontal: 10,
    backgroundColor: colors.ivory,
    borderTopWidth: 1,
    borderTopColor: colors.line,
  },
  item: { flex: 1, alignItems: 'center', gap: 4 },
  label: { fontFamily: 'Inter_400Regular', fontSize: 8.5, letterSpacing: 0.2 },
  centralItem: { flex: 1, alignItems: 'center', gap: 5 },
  plus: {
    width: 44,
    height: 44,
    borderRadius: radius.pill,
    backgroundColor: colors.ink,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: -20,
    shadowColor: colors.ink,
    shadowOpacity: 0.4,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 8 },
    elevation: 6,
  },
  centralLabel: { fontFamily: 'Inter_400Regular', fontSize: 8.5, color: colors.ink, letterSpacing: 0.2 },
});
