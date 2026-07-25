import { router } from 'expo-router';
import { useState } from 'react';
import { Pressable } from 'react-native';

import { AuthScaffold } from '@/components/auth/AuthScaffold';
import { AppText } from '@/components/ui/AppText';
import { Button } from '@/components/ui/Button';
import { Field } from '@/components/ui/Field';
import { useAuthStore } from '@/stores/auth';
import { colors } from '@/theme/ame';
import { toFormErrors } from '@/utils/errors';

const RENDERED = ['codigo', 'email', 'password'];

export default function Codigo() {
  const registrar = useAuthStore((s) => s.registrar);

  const [codigo, setCodigo] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [general, setGeneral] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    if (loading) return;
    setGeneral(null);

    const locales: Record<string, string> = {};
    if (!codigo.trim()) locales.codigo = 'Ingresá tu código de invitación';
    if (!email.trim()) locales.email = 'Ingresá tu email';
    if (!password) locales.password = 'Elegí una contraseña';
    setErrors(locales);
    if (Object.keys(locales).length) return;

    setLoading(true);
    try {
      await registrar({ email: email.trim(), password, codigo: codigo.trim() });
      // El gate de auth (Stack.Protected) redirige a las tabs automáticamente.
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
      title="Ingresá con tu código"
      subtitle="Usá el código de invitación que te dio el centro para activar tu cuenta."
      error={general}
      footer={
        <Pressable onPress={() => router.replace('/login')} hitSlop={8} accessibilityRole="button">
          <AppText variant="meta">
            ¿Ya tenés cuenta?{' '}
            <AppText variant="meta" color={colors.ink}>
              Iniciar sesión
            </AppText>
          </AppText>
        </Pressable>
      }>
      <Field
        label="Código de invitación"
        value={codigo}
        onChangeText={setCodigo}
        error={errors.codigo}
        placeholder="AME-XXXX-XXXX"
        autoCapitalize="characters"
        autoCorrect={false}
        returnKeyType="next"
      />
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
        placeholder="Elegí una contraseña"
        secureTextEntry
        autoCapitalize="none"
        textContentType="newPassword"
        returnKeyType="done"
        onSubmitEditing={submit}
      />
      <Button label="Activar mi cuenta" onPress={submit} loading={loading} />
    </AuthScaffold>
  );
}
