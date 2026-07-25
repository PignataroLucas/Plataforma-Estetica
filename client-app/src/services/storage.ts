/**
 * Persistencia segura y cross-platform para los tokens de sesión.
 *
 * En nativo (iOS/Android) usa `expo-secure-store` (Keychain / Keystore).
 * En web SecureStore no existe, así que caemos a `localStorage`.
 *
 * Guardamos SOLO los tokens (cada uno bien por debajo del límite histórico
 * de ~2KB de SecureStore en iOS). El perfil se re-consulta a `/perfil/` al
 * hidratar, así nunca queda desactualizado en el dispositivo.
 */
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

const isWeb = Platform.OS === 'web';

export async function getItem(key: string): Promise<string | null> {
  if (isWeb) {
    try {
      return globalThis.localStorage?.getItem(key) ?? null;
    } catch {
      return null;
    }
  }
  return SecureStore.getItemAsync(key);
}

export async function setItem(key: string, value: string): Promise<void> {
  if (isWeb) {
    try {
      globalThis.localStorage?.setItem(key, value);
    } catch {
      /* modo privado / sin storage: la sesión no persiste, no es fatal */
    }
    return;
  }
  await SecureStore.setItemAsync(key, value);
}

export async function deleteItem(key: string): Promise<void> {
  if (isWeb) {
    try {
      globalThis.localStorage?.removeItem(key);
    } catch {
      /* noop */
    }
    return;
  }
  await SecureStore.deleteItemAsync(key);
}
