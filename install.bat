@echo off
setlocal
echo ==================================================
echo ⚡ PhantomMirror Windows Bootstrapper
echo ==================================================
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" %*
endlocal
