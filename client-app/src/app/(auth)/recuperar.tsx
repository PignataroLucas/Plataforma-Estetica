/**
 * Paso 1 de recuperar la contraseña: pedir el código.
 *
 * El mensaje de éxito es deliberadamente ambiguo —"si hay una cuenta con ese
 * email"— porque el backend responde igual exista o no la cuenta. Prometer que
 * el mail salió cuando quizás no hay cuenta convertiría esta pantalla en un
 * detector de clientas del centro, que es justo lo que el endpoint evita.
 */
import { router } from 'expo-router';
import { useState } from 'react';

import { AuthScaffold } from '@/components/auth/AuthScaffold';
import { Button } from '@/components/ui/Button';
import { Field } from '@/components/ui/Field';
import { pedirCodigoRecuperacion } from '@/services/auth';
import { toFormErrors } from '@/utils/errors';

const RENDERED = ['email'];

export default function Recuperar() {
  const [email, setEmail] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [general, setGeneral] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    if (loading) return;
    setGeneral(null);

    const limpio = email.trim();
    if (!limpio) {
      setErrors({ email: 'Ingresá tu email' });
      return;
    }
    setErrors({});

    setLoading(true);
    try {
      await pedirCodigoRecuperacion(limpio);
      // Se pasa el email para que no tenga que volver a escribirlo.
      router.push({ pathname: '/nueva-clave', params: { email: limpio } });
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
      title="Recuperar contraseña"
      subtitle="Te mandamos un código de 6 dígitos al email de tu cuenta."
      error={general}>
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
        returnKeyType="done"
        onSubmitEditing={submit}
      />
      <Button label="Enviarme el código" onPress={submit} loading={loading} />
    </AuthScaffold>
  );
}
