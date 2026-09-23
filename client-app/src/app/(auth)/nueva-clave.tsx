/**
 * Paso 2 de recuperar la contraseña: el código y la clave nueva.
 *
 * No inicia sesión al terminar, aunque podría: el backend no devuelve tokens
 * acá a propósito, para que un código de un solo uso no se convierta en un
 * camino de autenticación paralelo. La clienta entra por login, como siempre.
 */
import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { Pressable } from 'react-native';

import { AuthScaffold } from '@/components/auth/AuthScaffold';
import { AppText } from '@/components/ui/AppText';
import { Button } from '@/components/ui/Button';
import { Field } from '@/components/ui/Field';
import { restablecerClave } from '@/services/auth';
import { colors } from '@/theme/ame';
import { toFormErrors } from '@/utils/errors';

const RENDERED = ['codigo', 'password', 'email'];

export default function NuevaClave() {
  const params = useLocalSearchParams<{ email?: string }>();
  const email = (params.email ?? '').trim();

  const [codigo, setCodigo] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [general, setGeneral] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [listo, setListo] = useState(false);

  const submit = async () => {
    if (loading) return;
    setGeneral(null);

    const locales: Record<string, string> = {};
    if (!codigo.trim()) locales.codigo = 'Ingresá el código que te llegó';
    if (!password) locales.password = 'Elegí una contraseña nueva';
    setErrors(locales);
    if (Object.keys(locales).length) return;

    setLoading(true);
    try {
      await restablecerClave({ email, codigo: codigo.trim(), password });
      setListo(true);
    } catch (e) {
      const f = toFormErrors(e, RENDERED);
      setErrors(f.fields);
      setGeneral(f.general);
    } finally {
      setLoading(false);
    }
  };

  if (listo) {
    return (
      <AuthScaffold
        title="Contraseña actualizada"
        subtitle="Ya podés entrar con tu contraseña nueva.">
        <Button label="Iniciar sesión" onPress={() => router.replace('/login')} />
      </AuthScaffold>
    );
  }

  return (
    <AuthScaffold
      title="Tu código"
      subtitle={
        email
          ? `Escribí el código que te mandamos a ${email} y elegí una contraseña nueva.`
          : 'Escribí el código que te mandamos y elegí una contraseña nueva.'
      }
      error={general}
      footer={
        <Pressable
          onPress={() => router.replace('/recuperar')}
          hitSlop={8}
          accessibilityRole="button">
          <AppText variant="meta">
            ¿No te llegó?{' '}
            <AppText variant="meta" color={colors.ink}>
              Pedir otro código
            </AppText>
          </AppText>
        </Pressable>
      }>
      <Field
        label="Código"
        value={codigo}
        onChangeText={setCodigo}
        error={errors.codigo}
        placeholder="000000"
        keyboardType="number-pad"
        autoCapitalize="none"
        autoCorrect={false}
        maxLength={6}
        returnKeyType="next"
      />
      <Field
        label="Contraseña nueva"
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
      <Button label="Cambiar contraseña" onPress={submit} loading={loading} />
    </AuthScaffold>
  );
}
