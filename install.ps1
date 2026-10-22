# ==============================================================================
# ⚡ PhantomMirror - Production Grade Windows Installer (PowerShell)
# Automates dependency resolution (Python, ADB, Scrcpy), deployment,
# PATH configuration, and Desktop / Start Menu shortcut integration.
# ==============================================================================
[CmdletBinding()]
param(
    [Alias("d")]
    [string]$Dir = "$env:LOCALAPPDATA\PhantomMirror",
    [switch]$NoShortcuts,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

if ($Help) {
    Write-Host @"
Usage: install.ps1 [options]

Options:
  -Dir, -d <path>     Specify custom directory to install PhantomMirror (Default: %LOCALAPPDATA%\PhantomMirror)
  -NoShortcuts        Skip creating Desktop and Start Menu shortcuts
  -Help, -h           Display this help menu
"@
    exit 0
}

# Ensure TLS 1.2+ for downloads
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13

Write-Host ""
Write-Host "  _____  _                 _                   __  __ _                     " -ForegroundColor Cyan
Write-Host " |  __ \| |               | |                 |  \/  (_)                    " -ForegroundColor Cyan
Write-Host " | |__) | |__   __ _ _ __ | |_ ___  _ __ ___  | \  / |_ _ __ _ __ ___  _ __ " -ForegroundColor Cyan
Write-Host " |  ___/| '_ \ / _` | '_ \| __/ _ \| '_ ` _ \ | |\/| | | '__| '__/ _ \| '__|" -ForegroundColor Cyan
Write-Host " | |    | | | | (_| | | | | || (_) | | | | | || |  | | | |  | | | (_) | |   " -ForegroundColor Cyan
Write-Host " |_|    |_| |_|\__,_|_| |_|\__\___/|_| |_| |_||_|  |_|_|_|  |_|  \___/|_|   " -ForegroundColor Cyan
Write-Host "⚡ Production-Grade Mobile Mirroring Suite Installer for Windows" -ForegroundColor Green
Write-Host ""
Write-Host "[*] Target Installation Path: $Dir" -ForegroundColor Yellow

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# ------------------------------------------------------------------------------
# Step 1: Verify & Install Core Dependencies
# ------------------------------------------------------------------------------
Write-Host "`n[+] Step 1: Checking system dependencies..." -ForegroundColor Blue

# 1.1 Python Check
$hasPython = $false
try {
    $pyVer = & python --version 2>&1
    if ($LASTEXITCODE -eq 0 -or $pyVer -match "Python 3") {
        Write-Host "[✓] Python 3 Detected : $pyVer" -ForegroundColor Green
        $hasPython = $true
    }
} catch {}

if (-not $hasPython) {
    try {
        $pyVer = & py -3 --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[✓] Python Launcher Detected : $pyVer" -ForegroundColor Green
            $hasPython = $true
        }
    } catch {}
}

if (-not $hasPython) {
    Write-Host "[!] Python 3 not found in PATH." -ForegroundColor Yellow
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host "[*] Installing Python 3.12 via winget..." -ForegroundColor Cyan
        & winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements --silent
        # Refresh Path
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    } else {
        Write-Host "[-] Please install Python 3 from https://www.python.org/downloads/ and check 'Add python.exe to PATH'." -ForegroundColor Red
        exit 1
    }
}

# 1.2 ADB Check
$hasAdb = $false
try {
    $adbCmd = Get-Command adb -ErrorAction SilentlyContinue
    if ($adbCmd) {
        Write-Host "[✓] ADB Found in PATH  : $($adbCmd.Source)" -ForegroundColor Green
        $hasAdb = $true
    }
} catch {}

if (-not $hasAdb) {
    # Check default android SDK locations
    $stdAdb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
    if (Test-Path $stdAdb) {
        Write-Host "[✓] ADB Detected at   : $stdAdb" -ForegroundColor Green
        $hasAdb = $true
    }
}

if (-not $hasAdb) {
    Write-Host "[!] ADB missing. Resolving..." -ForegroundColor Yellow
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host "[*] Installing Android SDK Platform-Tools via winget..." -ForegroundColor Cyan
        & winget install -e --id Google.PlatformTools --accept-package-agreements --accept-source-agreements --silent
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    } else {
        Write-Host "[*] Downloading official Google Platform-Tools..." -ForegroundColor Cyan
        $zipUrl = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
        $zipFile = "$env:TEMP\platform-tools-windows.zip"
        Invoke-WebRequest -Uri $zipUrl -OutFile $zipFile -UseBasicParsing
        New-Item -ItemType Directory -Path "$Dir\platform-tools" -Force | Out-Null
        Expand-Archive -Path $zipFile -DestinationPath "$Dir" -Force
        Remove-Item -Path $zipFile -Force
        $hasAdb = $true
    }
}

# 1.3 Scrcpy Check
$hasScrcpy = $false
try {
    $scrcpyCmd = Get-Command scrcpy -ErrorAction SilentlyContinue
    if ($scrcpyCmd) {
        Write-Host "[✓] Scrcpy Found in PATH : $($scrcpyCmd.Source)" -ForegroundColor Green
        $hasScrcpy = $true
    }
} catch {}

if (-not $hasScrcpy) {
    $scrcpyPaths = @(
        "C:\scrcpy\scrcpy.exe",
        "C:\ProgramData\chocolatey\bin\scrcpy.exe",
        "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Genymobile.scrcpy_Microsoft.Winget.Source_8wekyb3d8bbwe\scrcpy.exe"
    )
    foreach ($p in $scrcpyPaths) {
        if (Test-Path $p) {
            Write-Host "[✓] Scrcpy Detected at : $p" -ForegroundColor Green
            $hasScrcpy = $true
            break
        }
    }
}

if (-not $hasScrcpy) {
    Write-Host "[!] Scrcpy missing. Resolving..." -ForegroundColor Yellow
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host "[*] Installing Scrcpy via winget..." -ForegroundColor Cyan
        & winget install -e --id Genymobile.scrcpy --accept-package-agreements --accept-source-agreements --silent
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    } else {
        Write-Host "[*] Downloading official Genymobile Scrcpy release..." -ForegroundColor Cyan
        $scrcpyUrl = "https://github.com/Genymobile/scrcpy/releases/download/v3.1/scrcpy-win64-v3.1.zip"
        $scrcpyZip = "$env:TEMP\scrcpy-win64.zip"
        Invoke-WebRequest -Uri $scrcpyUrl -OutFile $scrcpyZip -UseBasicParsing
        $extractDir = "$Dir\scrcpy"
        New-Item -ItemType Directory -Path $extractDir -Force | Out-Null
        Expand-Archive -Path $scrcpyZip -DestinationPath "$env:TEMP\scrcpy_temp" -Force
        $nestedDir = (Get-ChildItem -Path "$env:TEMP\scrcpy_temp\scrcpy-win64*" -Directory | Select-Object -First 1).FullName
        Copy-Item -Path "$nestedDir\*" -Destination $extractDir -Recurse -Force
        Remove-Item -Path "$env:TEMP\scrcpy_temp" -Recurse -Force
        Remove-Item -Path $scrcpyZip -Force
        $hasScrcpy = $true
    }
}

# ------------------------------------------------------------------------------
# Step 2: Deploy PhantomMirror Files
# ------------------------------------------------------------------------------
Write-Host "`n[+] Step 2: Deploying PhantomMirror suite..." -ForegroundColor Blue
New-Item -ItemType Directory -Path $Dir -Force | Out-Null

$itemsToCopy = @("phantom", "phantom.cmd", "phantom.bat", "phantom.ps1", "phantom_frame.py", "assets", "protocol", "tools", "phantom-server")
foreach ($item in $itemsToCopy) {
    $src = Join-Path $ScriptDir $item
    if (Test-Path $src) {
        Copy-Item -Path $src -Destination $Dir -Recurse -Force
    }
}

Write-Host "[✓] Core suite deployed to $Dir" -ForegroundColor Green

# ------------------------------------------------------------------------------
# Step 3: Add to User PATH
# ------------------------------------------------------------------------------
Write-Host "`n[+] Step 3: Configuring PATH environment variable..." -ForegroundColor Blue
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($null -eq $userPath) { $userPath = "" }
$escapedDir = [regex]::Escape($Dir)

if ($userPath -notmatch "(^|;)$escapedDir(;|\$)") {
    $newUserPath = "$userPath;$Dir".Trim(';')
    [Environment]::SetEnvironmentVariable("Path", $newUserPath, "User")
    Write-Host "[✓] Added $Dir to User PATH" -ForegroundColor Green
} else {
    Write-Host "[✓] Directory is already in User PATH" -ForegroundColor Green
}

# Update current session PATH
if ($env:Path -notmatch "(^|;)$escapedDir(;|\$)") {
    $env:Path = "$Dir;$env:Path"
}

# ------------------------------------------------------------------------------
# Step 4: Create Desktop & Start Menu Shortcuts
# ------------------------------------------------------------------------------
if (-not $NoShortcuts) {
    Write-Host "`n[+] Step 4: Creating Windows shortcuts & Start Menu integration..." -ForegroundColor Blue
    try {
        $WshShell = New-Object -ComObject WScript.Shell
        $icoFile = Join-Path $Dir "assets\icon.ico"

        # Desktop Shortcut
        $desktopDir = [Environment]::GetFolderPath("Desktop")
        $desktopLnk = Join-Path $desktopDir "PhantomMirror.lnk"
        $shortcut = $WshShell.CreateShortcut($desktopLnk)
        $shortcut.TargetPath = "powershell.exe"
        $shortcut.Arguments = "-WindowStyle Hidden -ExecutionPolicy Bypass -Command `"& '$Dir\phantom.ps1' --gui`""
        if (Test-Path $icoFile) {
            $shortcut.IconLocation = "$icoFile,0"
        }
        $shortcut.Description = "PhantomMirror - Ultra Low-Latency Mobile Suite"
        $shortcut.WorkingDirectory = $Dir
        $shortcut.Save()
        Write-Host "[✓] Desktop shortcut created" -ForegroundColor Green

        # Start Menu Shortcut
        $startMenuDir = [Environment]::GetFolderPath("Programs")
        $startMenuLnk = Join-Path $startMenuDir "PhantomMirror.lnk"
        $shortcut2 = $WshShell.CreateShortcut($startMenuLnk)
        $shortcut2.TargetPath = "powershell.exe"
        $shortcut2.Arguments = "-WindowStyle Hidden -ExecutionPolicy Bypass -Command `"& '$Dir\phantom.ps1' --gui`""
        if (Test-Path $icoFile) {
            $shortcut2.IconLocation = "$icoFile,0"
        }
        $shortcut2.Description = "PhantomMirror - Ultra Low-Latency Mobile Suite"
        $shortcut2.WorkingDirectory = $Dir
        $shortcut2.Save()
        Write-Host "[✓] Start Menu shortcut created" -ForegroundColor Green
    } catch {
        Write-Host "[!] Notice: Could not create desktop shortcuts automatically ($($_.Exception.Message))" -ForegroundColor Yellow
    }
}

# ------------------------------------------------------------------------------
# Step 5: Verification & Completion
# ------------------------------------------------------------------------------
Write-Host "`n[+] Step 5: Running diagnostics..." -ForegroundColor Blue
try {
    & python "$Dir\phantom" doctor
} catch {
    Write-Host "[!] Could not run doctor automatically. You can test by typing 'phantom doctor'." -ForegroundColor Yellow
}

Write-Host @"
==================================================
🎉 PhantomMirror Production Build: INSTALLED ON WINDOWS!
==================================================
You can launch PhantomMirror anytime via:
  1. Desktop / Start Menu : Click on 'PhantomMirror'
  2. Terminal (PowerShell / Command Prompt):
     phantom --profile pro --wireless   (120 FPS / Apple Display Silhouette)
     phantom --virtual-session          (Independent locked-screen session)
     phantom doctor                     (System & hardware verification)
==================================================
"@ -ForegroundColor Green
