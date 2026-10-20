#!/usr/bin/env bash
# ==============================================================================
# ⚡ PhantomMirror - Uninstaller
# ==============================================================================
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BOLD='\033[1m'
NC='\033[0m'

if [ "$EUID" -eq 0 ] || (command -v sudo &> /dev/null && sudo -n true 2>/dev/null); then
    SUDO="sudo"
    INSTALL_DIR="/usr/local/share/phantom-mirror"
    BIN_DIR="/usr/local/bin"
    DESKTOP_FILE="/usr/share/applications/phantom-mirror.desktop"
    ICON_BASE="/usr/share/icons/hicolor"
else
    SUDO=""
    INSTALL_DIR="$HOME/.local/share/phantom-mirror"
    BIN_DIR="$HOME/.local/bin"
    DESKTOP_FILE="$HOME/.local/share/applications/phantom-mirror.desktop"
    ICON_BASE="$HOME/.local/share/icons/hicolor"
fi

echo -e "${RED}[*] Uninstalling PhantomMirror...${NC}"

$SUDO rm -rf "$INSTALL_DIR"
$SUDO rm -f "$BIN_DIR/phantom" "$BIN_DIR/phantom-mirror"
$SUDO rm -f "$DESKTOP_FILE"

for size in 48 64 128 256 512; do
    $SUDO rm -f "$ICON_BASE/${size}x${size}/apps/phantom-mirror.png"
done
$SUDO rm -f "$ICON_BASE/scalable/apps/phantom-mirror.svg"

if command -v update-desktop-database &> /dev/null; then
    $SUDO update-desktop-database "$(dirname "$DESKTOP_FILE")" 2>/dev/null || true
fi

echo -e "${GREEN}[✓] PhantomMirror has been cleanly uninstalled.${NC}"
