import { router } from 'expo-router';
import { useState } from 'react';
import { Pressable, StyleSheet } from 'react-native';

import { AuthScaffold } from '@/components/auth/AuthScaffold';
import { AppText } from '@/components/ui/AppText';
import { Button } from '@/components/ui/Button';
import { Field } from '@/components/ui/Field';
import { useAuthStore } from '@/stores/auth';
import { colors } from '@/theme/ame';
import { toFormErrors } from '@/utils/errors';

const RENDERED = ['email', 'password'];

export default function Login() {
  const iniciarSesion = useAuthStore((s) => s.iniciarSesion);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [general, setGeneral] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    if (loading) return;
    setGeneral(null);

    const locales: Record<string, string> = {};
    if (!email.trim()) locales.email = 'Ingresá tu email';
    if (!password) locales.password = 'Ingresá tu contraseña';
    setErrors(locales);
    if (Object.keys(locales).length) return;

    setLoading(true);
    try {
      await iniciarSesion(email.trim(), password);
      // El gate de auth redirige a las tabs automáticamente.
    } catch (e) {
      const f = toFormErrors(e, RENDERED);
      setErrors(f.fields);
      setGeneral(f.general);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthScaffold
      title="Iniciar sesión"
      subtitle="Ingresá con el email y la contraseña de tu cuenta."
      error={general}
      footer={
        <Pressable onPress={() => router.replace('/codigo')} hitSlop={8} accessibilityRole="button">
          <AppText variant="meta">
            ¿Tenés un código de invitación?{' '}
            <AppText variant="meta" color={colors.ink}>
              Activá tu cuenta
            </AppText>
          </AppText>
        </Pressable>
      }>
      <Field
        label="Email"
        value={email}
        onChangeText={setEmail}
        error={errors.email}
        placeholder="tu@email.com"
        autoCapitalize="none"
        autoCorrect={false}
        keyboardType="email-address"
        textContentType="emailAddress"
        returnKeyType="next"
      />
      <Field
        label="Contraseña"
        value={password}
        onChangeText={setPassword}
        error={errors.password}
        placeholder="Tu contraseña"
        secureTextEntry
        autoCapitalize="none"
        textContentType="password"
        returnKeyType="done"
        onSubmitEditing={submit}
      />
      <Button label="Ingresar" onPress={submit} loading={loading} />
      <Pressable
        onPress={() => router.push('/recuperar')}
        hitSlop={8}
        style={styles.olvide}
        accessibilityRole="button">
        <AppText variant="meta">¿Olvidaste tu contraseña?</AppText>
      </Pressable>
    </AuthScaffold>
  );
}

const styles = StyleSheet.create({
  olvide: { alignItems: 'center', paddingVertical: 4 },
});
