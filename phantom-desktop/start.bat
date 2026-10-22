@echo off
setlocal
echo ==================================================
echo ⚡ Starting PhantomMirror Desktop & Stream Bridge (Windows)
echo ==================================================
cd /d "%~dp0"

echo [*] Starting Stream Bridge on ws://localhost:49153...
start "Phantom Stream Bridge" cmd /c "node stream-bridge.js"

echo [*] Starting Vite Frontend...
start "Phantom Desktop UI" cmd /c "npm run dev"

echo ==================================================
echo [✓] Development servers launched in background windows.
echo [*] Navigate to http://localhost:1420 or http://localhost:5173
echo ==================================================
endlocal
