# ==============================================================================
# ⚡ PhantomMirror - Android Deployment Utility (PowerShell)
# ==============================================================================
param(
    [string]$Port = "49152"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServerJar = Join-Path $ScriptDir "phantom-server\build\phantom-server.jar"
$RemoteTmp = "/data/local/tmp/phantom-server.jar"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "⚡ PhantomMirror Android Deployer (Windows)" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

if (-not (Test-Path $ServerJar)) {
    $found = Get-ChildItem -Path (Join-Path $ScriptDir "phantom-server") -Filter "*.jar" -Recurse | Select-Object -First 1
    if ($found) {
        $ServerJar = $found.FullName
    } else {
        Write-Host "[-] Error: phantom-server.jar missing from phantom-server\build." -ForegroundColor Red
        exit 1
    }
}

if (-not (Get-Command adb -ErrorAction SilentlyContinue)) {
    Write-Host "[-] Error: 'adb' command not found in PATH." -ForegroundColor Red
    Write-Host "[!] Install via: winget install Google.PlatformTools" -ForegroundColor Yellow
    exit 1
}

Write-Host "[+] Checking for connected devices..." -ForegroundColor Blue
$devOut = & adb devices | Select-String -NotMatch "List" | Select-String "device"
if (-not $devOut) {
    Write-Host "[-] No Android device detected via ADB." -ForegroundColor Red
    Write-Host "[!] Connect your phone via USB or Wi-Fi with USB Debugging enabled." -ForegroundColor Yellow
    exit 1
}

Write-Host "[+] Target device ready." -ForegroundColor Green
Write-Host "[+] Pushing $ServerJar -> $RemoteTmp..." -ForegroundColor Cyan
& adb push "$ServerJar" "$RemoteTmp"

Write-Host "[+] Starting PhantomMirror server daemon on port $Port..." -ForegroundColor Green
Write-Host "[*] Press Ctrl+C to stop the remote daemon." -ForegroundColor Yellow
Write-Host "==================================================" -ForegroundColor Cyan

& adb shell CLASSPATH="$RemoteTmp" app_process / com.phantom.mirror.PhantomServer $Port
