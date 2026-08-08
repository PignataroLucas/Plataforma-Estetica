# Correr la app AME en el emulador Android

Guía para levantar la app `client-app` en el emulador Android de esta máquina.
Los comandos son para **PowerShell** (Windows).

---

## ⚡ La forma fácil (un solo comando)

**1. Levantá el backend** (desde la raíz del repo, en otra terminal):

```powershell
docker-compose up
```

**2. Levantá la app** (desde `client-app/`):

```powershell
cd client-app
.\correr-app.cmd
```

> También podés usar `npm run emu` (hace lo mismo).

Ese comando hace **todo solo**: bootea el emulador, espera a que arranque, lo
conecta al backend (`adb reverse`) y arranca Expo. Dejá esa ventana abierta.

- La **primera vez** instala Expo Go en el emulador (~100 MB) y abre la app.
- Cuando guardás un archivo, la app recarga sola (Fast Refresh).
- Para frenar: `Ctrl+C` en esa ventana. Para volver a arrancar: corré `.\correr-app.cmd` de nuevo.

> ℹ️ Si el emulador ya está abierto, el script lo detecta y no abre otro.

---

## Qué ya está instalado (no hace falta reinstalar)

| Componente | Ubicación / valor |
|---|---|
| Android SDK | `%LOCALAPPDATA%\Android\Sdk` |
| JDK 17 | `%LOCALAPPDATA%\Android\jdk-17.0.19+10` |
| AVD (dispositivo virtual) | **`ame_pixel`** (Android 15) |
| adb | `%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe` |
| emulator | `%LOCALAPPDATA%\Android\Sdk\emulator\emulator.exe` |

---

## 🌐 Alternativa: en el navegador (sin emulador)

Para iterar diseño más rápido, sin bootear el emulador:

```powershell
cd client-app
npx expo start --web
```

Abre en `http://localhost:8081`. No valida cosas nativas (safe areas, gestos),
pero es más ágil para el diseño.

---

## 🔧 Modo manual (paso a paso, si el script falla)

> **IMPORTANTE:** en PowerShell, para ejecutar un `.exe` cuya ruta va entre
> comillas, tenés que poner el operador **`&`** adelante. Si lo omitís, PowerShell
> cree que es texto y tira `Unexpected token '-avd'...`. **Siempre el `&` al inicio.**

**1. Backend** (raíz del repo): `docker-compose up`

**2. Bootear el emulador:**

```powershell
& "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe" -avd ame_pixel -gpu swiftshader_indirect
```

Esperá 1–2 min a que llegue al home de Android. Dejá esa ventana abierta.

**3. Conectar el emulador al backend** (en otra terminal):

```powershell
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" reverse tcp:8000 tcp:8000
```

Sin esto la app no trae datos. Se pierde si reiniciás el emulador → volvé a correrlo.

**4. Levantar la app:**

```powershell
cd client-app
npx expo start --android
```

---

## Comandos útiles

Definí una variable corta para adb en tu sesión de PowerShell:

```powershell
$adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
```

| Acción | Comando |
|---|---|
| Ver dispositivos conectados | `& $adb devices` |
| Screenshot del emulador | `& $adb exec-out screencap -p > captura.png` |
| Ver los `reverse` activos | `& $adb reverse --list` |
| Reabrir la app | en la terminal de Expo, tecla `r` |
| Listar los AVDs | `& "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe" -list-avds` |

---

## Problemas comunes

- **`Unexpected token '-avd' in expression or statement`** → falta el **`&`** al
  principio del comando (ver el recuadro de arriba), o simplemente usá `.\correr-app.cmd`.
- **`correr-app.cmd` no hace nada / se cierra al toque** → abrilo desde una terminal
  (no doble click) para ver el mensaje de error. Suele ser que falta el backend o el SDK.
- **`no devices/emulators found`** → el emulador no terminó de bootear todavía, o se
  cerró. Esperá al home de Android, o corré `.\correr-app.cmd` de nuevo (rebootea si hace falta).
- **La app no trae datos del backend** → falta `adb reverse tcp:8000 tcp:8000` (el script
  lo hace solo) o el backend no está `up`. Probá abrir
  `http://localhost:8000/api/public/centros/1/servicios/` en el navegador del host.
- **"Cannot connect to Expo CLI" en la app** → suele pasar si reiniciaste Metro a mitad
  de sesión. Cerrá Expo Go (force-stop) y reabrí, o corré `.\correr-app.cmd` de nuevo.
- **El emulador no bootea / pantalla negra** → el script usa `-gpu swiftshader_indirect`
  (render por software, estable). Verificá que no haya otro hipervisor (LDPlayer, etc.) abierto.
- **Puerto 8081 ocupado** → matá el proceso viejo:
  `Get-NetTCPConnection -LocalPort 8081 -State Listen | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }`

---

## Development build (necesario para notificaciones)

El flujo de arriba usa **Expo Go**, que no requiere compilar nativo ni
`JAVA_HOME`. Pero Expo Go **no sirve para notificaciones**: desde el SDK 53
`expo-notifications` ni siquiera se puede importar en Expo Go sobre Android
(lanza una excepción al cargar el módulo). Para probar avisos hace falta un
development build.

```powershell
cd client-app
$env:JAVA_HOME = "$env:LOCALAPPDATA\Android\jdk-17.0.19+10"
npx expo run:android --port 8082
```

> **El `--port 8082` es a propósito:** si dejás corriendo la sesión de Expo Go en
> el 8081, sin ese flag el comando pregunta de forma interactiva y se traba.

Notas:

- **Verificá que `JAVA_HOME` haya quedado seteado en la misma terminal** antes de
  correr el comando (`echo $env:JAVA_HOME`). Si Gradle dice `JAVA_HOME is set to
  an invalid directory` con un path que sí existe, casi siempre es que la
  variable no se propagó al proceso hijo: seteala y corré el build como dos
  comandos separados en esa misma ventana, no encadenados.
- No persistas `JAVA_HOME` globalmente para no pisar el Java 8 del sistema.
- La primera compilación baja Gradle y las dependencias de Android: tarda bastante.
  Las siguientes usan cache.
- `expo run:android` genera el directorio `android/` (está en `.gitignore`, no se
  commitea) y agrega `android.package` en `app.json`.
