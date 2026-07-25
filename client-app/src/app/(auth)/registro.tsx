import { router } from 'expo-router';
import { useState } from 'react';
import { Pressable, View } from 'react-native';

import { AuthScaffold } from '@/components/auth/AuthScaffold';
import { AppText } from '@/components/ui/AppText';
import { Button } from '@/components/ui/Button';
import { Field } from '@/components/ui/Field';
import { DEFAULT_CENTRO_ID } from '@/services/config';
import { useAuthStore } from '@/stores/auth';
import { colors, spacing } from '@/theme/ame';
import { toFormErrors } from '@/utils/errors';

const RENDERED = ['nombre', 'apellido', 'email', 'telefono', 'password'];

export default function Registro() {
  const registrar = useAuthStore((s) => s.registrar);

  const [nombre, setNombre] = useState('');
  const [apellido, setApellido] = useState('');
  const [email, setEmail] = useState('');
  const [telefono, setTelefono] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [general, setGeneral] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    if (loading) return;
    setGeneral(null);

    const locales: Record<string, string> = {};
    if (!nombre.trim()) locales.nombre = 'Ingresá tu nombre';
    if (!apellido.trim()) locales.apellido = 'Ingresá tu apellido';
    if (!email.trim()) locales.email = 'Ingresá tu email';
    if (!password) locales.password = 'Elegí una contraseña';
    setErrors(locales);
    if (Object.keys(locales).length) return;

    setLoading(true);
    try {
      await registrar({
        email: email.trim(),
        password,
        nombre: nombre.trim(),
        apellido: apellido.trim(),
        telefono: telefono.trim() || undefined,
        centro: DEFAULT_CENTRO_ID,
      });
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
      title="Crear tu cuenta"
      subtitle="Registrate para reservar turnos y acceder a tus beneficios."
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
      <View style={styles.row}>
        <View style={styles.col}>
          <Field
            label="Nombre"
            value={nombre}
            onChangeText={setNombre}
            error={errors.nombre}
            autoCapitalize="words"
            textContentType="givenName"
            returnKeyType="next"
          />
        </View>
        <View style={styles.col}>
          <Field
            label="Apellido"
            value={apellido}
            onChangeText={setApellido}
            error={errors.apellido}
            autoCapitalize="words"
            textContentType="familyName"
            returnKeyType="next"
          />
        </View>
      </View>
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
        label="Teléfono (opcional)"
        value={telefono}
        onChangeText={setTelefono}
        error={errors.telefono}
        placeholder="11 5555 5555"
        keyboardType="phone-pad"
        textContentType="telephoneNumber"
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
      <Button label="Crear cuenta" onPress={submit} loading={loading} />
    </AuthScaffold>
  );
}

const styles = {
  row: { flexDirection: 'row', gap: spacing.md } as const,
  col: { flex: 1 } as const,
};
