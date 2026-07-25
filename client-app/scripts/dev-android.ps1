# Levanta la app AME en el emulador Android con un solo comando:
#   1. bootea el emulador (si no hay uno conectado)
#   2. espera a que Android termine de arrancar
#   3. conecta el emulador al backend (adb reverse tcp:8000)
#   4. arranca la app (Expo / Metro)
#
# Se usa via  correr-app.cmd  o  npm run emu  (ver CORRER_EN_EMULADOR.md).
# Requiere el backend levantado aparte:  docker-compose up

$ErrorActionPreference = 'Stop'

$sdk      = Join-Path $env:LOCALAPPDATA 'Android\Sdk'
$adb      = Join-Path $sdk 'platform-tools\adb.exe'
$emulator = Join-Path $sdk 'emulator\emulator.exe'
$avd      = 'ame_pixel'

function Fail($msg) { Write-Host "ERROR: $msg" -ForegroundColor Red; exit 1 }

if (-not (Test-Path $adb))      { Fail "No encuentro adb en $adb. Revisa que el Android SDK este instalado." }
if (-not (Test-Path $emulator)) { Fail "No encuentro el emulator en $emulator." }

# 1) Emulador: bootear solo si no hay ya un device conectado
if ((& $adb devices) -match 'emulator-\d+\s+device') {
    Write-Host 'OK  Emulador ya conectado.' -ForegroundColor Green
} else {
    Write-Host '->  Booteando el emulador ame_pixel (se abre en otra ventana)...' -ForegroundColor Cyan
    Start-Process -FilePath $emulator -ArgumentList '-avd', $avd, '-gpu', 'swiftshader_indirect'
}

# 2) Esperar a que Android termine de arrancar (timeout 3 min)
Write-Host '->  Esperando a que Android arranque (puede tardar 1-2 min)...' -ForegroundColor Cyan
& $adb wait-for-device
$deadline = (Get-Date).AddMinutes(3)
while ("$(& $adb shell getprop sys.boot_completed 2>$null)".Trim() -ne '1') {
    if ((Get-Date) -gt $deadline) { Fail 'El emulador tardo demasiado en arrancar. Cerralo y proba de nuevo.' }
    Start-Sleep -Seconds 2
}
Write-Host 'OK  Emulador listo.' -ForegroundColor Green

# 3) Conectar el emulador al backend (localhost:8000 dentro del emulador -> host)
& $adb reverse tcp:8000 tcp:8000 | Out-Null
Write-Host 'OK  adb reverse tcp:8000 (backend conectado).' -ForegroundColor Green

# 4) Arrancar la app. Esta ventana queda ocupada con Expo/Metro (dejala abierta).
Set-Location (Join-Path $PSScriptRoot '..')
Write-Host '->  Iniciando Expo... (deja esta ventana abierta; Ctrl+C para frenar)' -ForegroundColor Cyan
npx expo start --android
