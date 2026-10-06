import { Feather } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useState } from 'react';
import { StyleSheet, View } from 'react-native';

import { AuthScaffold } from '@/components/auth/AuthScaffold';
import { AppText } from '@/components/ui/AppText';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Field } from '@/components/ui/Field';
import { useAuthStore } from '@/stores/auth';
import { colors, spacing } from '@/theme/ame';
import { toFormErrors } from '@/utils/errors';

const RENDERED = ['password'];

/**
 * Baja de la cuenta, como exige Google Play.
 *
 * La pantalla dice con todas las letras qué se borra y qué no, porque la
 * diferencia no es obvia: la cuenta de la app es de la clienta, pero la ficha
 * con sus tratamientos es del centro y queda (ver
 * `backend/apps/clientes/cuenta_app.py`). Si no lo dijera, "eliminar mi cuenta"
 * prometería algo que no hace.
 *
 * Pide la contraseña porque no se puede deshacer: un teléfono desbloqueado en
 * manos ajenas no puede alcanzar para borrarle la cuenta a nadie.
 */
export default function EliminarCuenta() {
  const usuario = useAuthStore((s) => s.usuario);
  const eliminarCuenta = useAuthStore((s) => s.eliminarCuenta);

  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [general, setGeneral] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const centros = (usuario?.vinculaciones ?? []).map((v) => v.centro_nombre);
  const elCentro = centros.length === 1 ? centros[0] : 'el centro';

  const submit = async () => {
    if (loading) return;
    setGeneral(null);
    if (!password) {
      setErrors({ password: 'Ingresá tu contraseña' });
      return;
    }
    setErrors({});

    setLoading(true);
    try {
      await eliminarCuenta(password);
      // Sin sesión, el gate de navegación la lleva a la bienvenida solo.
    } catch (e) {
      const f = toFormErrors(e, RENDERED);
      setErrors(f.fields);
      setGeneral(f.general);
      setLoading(false);
    }
  };

  return (
    <AuthScaffold
      title="Eliminar mi cuenta"
      subtitle="Esto no se puede deshacer."
      error={general}>
      <Card style={styles.card}>
        <AppText variant="label">Se borra</AppText>
        <Linea icono="x" texto="Tu cuenta de la app: el email y la contraseña con que entrás." />
        <Linea icono="x" texto="Los avisos: tus teléfonos registrados y tus preferencias." />
        {centros.length > 0 ? (
          <Linea icono="x" texto={`El vínculo con ${centros.join(', ')}.`} />
        ) : null}
      </Card>

      <Card style={styles.card}>
        <AppText variant="label">Queda en {elCentro}</AppText>
        <Linea
          icono="check"
          texto="Tu ficha, con tus tratamientos y turnos. Es del centro, que la necesita para seguir atendiéndote."
        />
        <AppText variant="meta" style={styles.nota}>
          Si querés que también la borren, pedíselo directamente a {elCentro}.
        </AppText>
      </Card>

      <Field
        label="Contraseña"
        value={password}
        onChangeText={setPassword}
        error={errors.password}
        placeholder="Para confirmar que sos vos"
        secureTextEntry
        autoCapitalize="none"
        autoCorrect={false}
        textContentType="password"
        returnKeyType="done"
        onSubmitEditing={submit}
      />

      <Button label="Eliminar mi cuenta" variant="danger" loading={loading} onPress={submit} />
      <Button label="Cancelar" variant="ghost" disabled={loading} onPress={() => router.back()} />
    </AuthScaffold>
  );
}

function Linea({ icono, texto }: { icono: 'x' | 'check'; texto: string }) {
  return (
    <View style={styles.linea}>
      <Feather
        name={icono}
        size={15}
        color={icono === 'x' ? colors.danger : colors.muted}
        style={styles.icono}
      />
      <AppText variant="body" style={styles.lineaTxt}>
        {texto}
      </AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  card: { gap: spacing.md },
  linea: { flexDirection: 'row', gap: spacing.sm },
  icono: { marginTop: 2 },
  lineaTxt: { flex: 1, lineHeight: 20 },
  nota: { lineHeight: 16 },
});
