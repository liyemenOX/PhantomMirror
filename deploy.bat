@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "SERVER_JAR=%SCRIPT_DIR%phantom-server\build\phantom-server.jar"
set "REMOTE_TMP=/data/local/tmp/phantom-server.jar"
set "PORT=%~1"
if "%PORT%"=="" set "PORT=49152"

echo ==================================================
echo ⚡ PhantomMirror Android Deployer (Windows)
echo ==================================================

if not exist "%SERVER_JAR%" (
    echo [!] Pre-built phantom-server.jar not found at %SERVER_JAR%
    echo [*] Attempting to locate server jar in phantom-server...
    for /r "%SCRIPT_DIR%phantom-server" %%F in (*.jar) do (
        set "SERVER_JAR=%%F"
        goto :found_jar
    )
    echo [-] Error: phantom-server.jar missing. Build it first or check phantom-server/build.
    exit /b 1
)

:found_jar
where adb >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [-] Error: 'adb' command not found in PATH.
    echo [!] Install via: winget install Google.PlatformTools
    exit /b 1
)

echo [+] Checking for connected devices...
for /f "tokens=*" %%D in ('adb devices ^| findstr /v "List" ^| findstr "device"') do (
    set "DEVICE_FOUND=1"
)

if not defined DEVICE_FOUND (
    echo [-] No Android device detected via ADB.
    echo [!] Connect your phone via USB or Wi-Fi with USB Debugging enabled.
    exit /b 1
)

echo [+] Target device ready.
echo [+] Pushing %SERVER_JAR% -^> %REMOTE_TMP%...
adb push "%SERVER_JAR%" "%REMOTE_TMP%"

echo [+] Starting PhantomMirror server daemon on port %PORT%...
echo [*] Press Ctrl+C to stop the remote daemon.
echo ==================================================

adb shell CLASSPATH="%REMOTE_TMP%" app_process / com.phantom.mirror.PhantomServer %PORT%
endlocal
