@echo off
setlocal
echo ==================================================
echo ⚡ PhantomMirror Windows Uninstaller
echo ==================================================
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0uninstall.ps1" %*
endlocal
