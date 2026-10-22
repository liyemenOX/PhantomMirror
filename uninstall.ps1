# ==============================================================================
# ⚡ PhantomMirror - Windows Uninstaller (PowerShell)
# ==============================================================================
[CmdletBinding()]
param(
    [Alias("d")]
    [string]$Dir = "$env:LOCALAPPDATA\PhantomMirror"
)

$ErrorActionPreference = "SilentlyContinue"

Write-Host "[*] Uninstalling PhantomMirror from Windows..." -ForegroundColor Yellow

# 1. Remove Shortcuts
$desktopDir = [Environment]::GetFolderPath("Desktop")
$desktopLnk = Join-Path $desktopDir "PhantomMirror.lnk"
if (Test-Path $desktopLnk) {
    Remove-Item -Path $desktopLnk -Force
    Write-Host "[✓] Removed Desktop shortcut" -ForegroundColor Green
}

$startMenuDir = [Environment]::GetFolderPath("Programs")
$startMenuLnk = Join-Path $startMenuDir "PhantomMirror.lnk"
if (Test-Path $startMenuLnk) {
    Remove-Item -Path $startMenuLnk -Force
    Write-Host "[✓] Removed Start Menu shortcut" -ForegroundColor Green
}

# 2. Remove from User PATH
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath) {
    $escapedDir = [regex]::Escape($Dir)
    $cleanPaths = ($userPath -split ';') | Where-Object { $_ -and $_ -notmatch "^$escapedDir\\?$" }
    $newUserPath = ($cleanPaths -join ';').Trim(';')
    [Environment]::SetEnvironmentVariable("Path", $newUserPath, "User")
    Write-Host "[✓] Removed $Dir from User PATH" -ForegroundColor Green
}

# 3. Remove Installed Files
if (Test-Path $Dir) {
    Remove-Item -Path $Dir -Recurse -Force
    Write-Host "[✓] Removed $Dir" -ForegroundColor Green
}

Write-Host "`n[✓] PhantomMirror has been cleanly uninstalled from Windows." -ForegroundColor Green
