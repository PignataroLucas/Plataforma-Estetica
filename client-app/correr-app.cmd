@echo off
REM Levanta la app AME en el emulador Android (emulador + adb reverse + Expo).
REM Doble click, o desde una terminal:  .\correr-app.cmd
REM (El backend va aparte:  docker-compose up)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\dev-android.ps1"
