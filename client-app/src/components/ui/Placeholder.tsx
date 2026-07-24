import { StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { colors, spacing } from '@/theme/ame';

import { AppText } from './AppText';

interface Props {
  title: string;
  subtitle?: string;
}

export function Placeholder({ title, subtitle }: Props) {
  return (
    <SafeAreaView style={styles.container}>
      <AppText variant="title">{title}</AppText>
      {subtitle ? (
        <AppText variant="meta" style={styles.subtitle}>
          {subtitle}
        </AppText>
      ) : null}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.ivory,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.xs,
    paddingHorizontal: spacing.xl,
  },
  subtitle: { textAlign: 'center' },
});
