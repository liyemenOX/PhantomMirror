#!/usr/bin/env bash
# ==============================================================================
# ⚡ PhantomMirror - Production Grade Installer
# Automates dependency resolution, system installation, desktop integration,
# and high-resolution icon deployment for Linux.
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${CYAN}${BOLD}"
cat << "EOF"
  _____  _                 _                   __  __ _                     
 |  __ \| |               | |                 |  \/  (_)                    
 | |__) | |__   __ _ _ __ | |_ ___  _ __ ___  | \  / |_ _ __ _ __ ___  _ __ 
 |  ___/| '_ \ / _` | '_ \| __/ _ \| '_ ` _ \ | |\/| | | '__| '__/ _ \| '__|
 | |    | | | | (_| | | | | || (_) | | | | | || |  | | | |  | | | (_) | |   
 |_|    |_| |_|\__,_|_| |_|\__\___/|_| |_| |_||_|  |_|_|_|  |_|  \___/|_|   
EOF
echo -e "${GREEN}⚡ Production-Grade Mobile Mirroring Suite Installer${NC}\n"

# Determine install scope (system-wide if root / sudo, otherwise user-local)
if [ "$EUID" -eq 0 ]; then
    INSTALL_DIR="/usr/local/share/phantom-mirror"
    BIN_DIR="/usr/local/bin"
    DESKTOP_DIR="/usr/share/applications"
    ICON_BASE_DIR="/usr/share/icons/hicolor"
    SUDO=""
else
    # Check if user has sudo privileges, otherwise install to ~/.local
    if command -v sudo &> /dev/null && sudo -n true 2>/dev/null; then
        INSTALL_DIR="/usr/local/share/phantom-mirror"
        BIN_DIR="/usr/local/bin"
        DESKTOP_DIR="/usr/share/applications"
        ICON_BASE_DIR="/usr/share/icons/hicolor"
        SUDO="sudo"
    else
        INSTALL_DIR="$HOME/.local/share/phantom-mirror"
        BIN_DIR="$HOME/.local/bin"
        DESKTOP_DIR="$HOME/.local/share/applications"
        ICON_BASE_DIR="$HOME/.local/share/icons/hicolor"
        SUDO=""
        mkdir -p "$BIN_DIR"
    fi
fi

echo -e "[*] Target Installation Prefix: ${BOLD}$BIN_DIR${NC}"

# 1. Dependency Verification & Auto-Installation
echo -e "\n${BLUE}[+] Step 1: Checking system dependencies...${NC}"

MISSING_PKGS=()
if ! command -v adb &> /dev/null; then
    MISSING_PKGS+=("adb")
fi
if ! command -v scrcpy &> /dev/null && [ ! -f "/snap/bin/scrcpy" ]; then
    MISSING_PKGS+=("scrcpy")
fi
if ! python3 -c "import Xlib" &> /dev/null; then
    MISSING_PKGS+=("python3-xlib")
fi
if ! python3 -c "import cairo" &> /dev/null; then
    MISSING_PKGS+=("python3-cairo")
fi
if ! python3 -c "import gi; gi.require_version('Gtk', '3.0')" &> /dev/null; then
    MISSING_PKGS+=("gir1.2-gtk-3.0")
fi

if [ ${#MISSING_PKGS[@]} -gt 0 ]; then
    echo -e "${YELLOW}[!] Missing packages detected: ${MISSING_PKGS[*]}${NC}"
    if command -v apt-get &> /dev/null; then
        echo -e "[*] Auto-installing missing dependencies via apt..."
        $SUDO apt-get update -qq
        $SUDO apt-get install -y -qq adb scrcpy python3-xlib python3-cairo python3-gi gir1.2-gtk-3.0 || true
    elif command -v pacman &> /dev/null; then
        $SUDO pacman -Sy --noconfirm android-tools scrcpy python-xlib python-cairo python-gobject gtk3 || true
    elif command -v dnf &> /dev/null; then
        $SUDO dnf install -y android-tools scrcpy python3-xlib python3-cairo python3-gobject gtk3 || true
    fi
else
    echo -e "${GREEN}[✓] All core dependencies verified!${NC}"
fi

# Ensure icons are generated
if [ ! -f "assets/icon_512.png" ]; then
    echo -e "[*] Generating application branding and icons..."
    python3 -c "
import math, cairo
def draw_icon(size, fn):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
    cr = cairo.Context(s)
    cr.scale(size/512.0, size/512.0)
    r = 110
    cr.new_sub_path()
    cr.arc(512-r, r, r, -math.pi/2, 0); cr.arc(512-r, 512-r, r, 0, math.pi/2)
    cr.arc(r, 512-r, r, math.pi/2, math.pi); cr.arc(r, r, r, math.pi, 3*math.pi/2)
    cr.close_path()
    pat = cairo.LinearGradient(0, 0, 512, 512)
    pat.add_color_stop_rgba(0, 0.04, 0.06, 0.08, 1.0)
    pat.add_color_stop_rgba(1, 0.08, 0.12, 0.16, 1.0)
    cr.set_source(pat); cr.fill_preserve()
    cr.set_source_rgba(0.0, 1.0, 0.45, 0.8); cr.set_line_width(8); cr.stroke()
    # Phone
    pw, ph, pr = 200, 380, 36
    px, py = (512-pw)/2, (512-ph)/2
    cr.new_sub_path()
    cr.arc(px+pw-pr, py+pr, pr, -math.pi/2, 0); cr.arc(px+pw-pr, py+ph-pr, pr, 0, math.pi/2)
    cr.arc(px+pr, py+ph-pr, pr, math.pi/2, math.pi); cr.arc(px+pr, py+pr, pr, math.pi, 3*math.pi/2)
    cr.close_path()
    cr.set_source_rgba(0.02, 0.03, 0.05, 0.95); cr.fill_preserve()
    cr.set_source_rgba(0.25, 0.35, 0.45, 0.7); cr.set_line_width(4); cr.stroke()
    # Bolt
    cr.move_to(266, 160); cr.line_to(205, 275); cr.line_to(250, 275)
    cr.line_to(236, 360); cr.line_to(315, 240); cr.line_to(270, 240); cr.close_path()
    cr.set_source_rgba(0.0, 1.0, 0.5, 1.0); cr.fill()
    s.write_to_png(fn)
import os; os.makedirs('assets', exist_ok=True)
for sz in [512, 256, 128, 64, 48]: draw_icon(sz, f'assets/icon_{sz}.png')
draw_icon(512, 'assets/icon.png')
"
fi

# 2. Deploy Application Assets
echo -e "\n${BLUE}[+] Step 2: Deploying PhantomMirror suite...${NC}"
$SUDO mkdir -p "$INSTALL_DIR"
$SUDO cp -r phantom phantom_frame.py assets "$INSTALL_DIR/"
$SUDO chmod +x "$INSTALL_DIR/phantom"
$SUDO chmod +x "$INSTALL_DIR/phantom_frame.py"

# Create symlink in bin
$SUDO ln -sf "$INSTALL_DIR/phantom" "$BIN_DIR/phantom"
$SUDO ln -sf "$INSTALL_DIR/phantom" "$BIN_DIR/phantom-mirror"

# 3. Deploy Desktop & Icon Integration
echo -e "\n${BLUE}[+] Step 3: Installing Desktop integration & system icons...${NC}"
$SUDO mkdir -p "$DESKTOP_DIR"
$SUDO cp assets/phantom-mirror.desktop "$DESKTOP_DIR/"
$SUDO chmod 644 "$DESKTOP_DIR/phantom-mirror.desktop"

# Install icons into hicolor theme
for size in 48 64 128 256 512; do
    ICON_DIR="$ICON_BASE_DIR/${size}x${size}/apps"
    $SUDO mkdir -p "$ICON_DIR"
    $SUDO cp "assets/icon_${size}.png" "$ICON_DIR/phantom-mirror.png"
done

# SVG icon
SVG_ICON_DIR="$ICON_BASE_DIR/scalable/apps"
$SUDO mkdir -p "$SVG_ICON_DIR"
$SUDO cp assets/icon.svg "$SVG_ICON_DIR/phantom-mirror.svg"

# Update caches
if command -v update-desktop-database &> /dev/null; then
    $SUDO update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi
if command -v gtk-update-icon-cache &> /dev/null; then
    $SUDO gtk-update-icon-cache -f -t "$ICON_BASE_DIR" 2>/dev/null || true
fi

echo -e "\n${GREEN}=================================================="
echo -e "🎉 PhantomMirror Production Build: INSTALLED!"
echo -e "==================================================${NC}"
echo -e "You can now launch PhantomMirror in two ways:"
echo -e "  1. ${BOLD}Desktop UI${NC}: Search for 'PhantomMirror' in your Application Menu or Dock."
echo -e "  2. ${BOLD}Terminal${NC}: Run anywhere:\n"
echo -e "     ${CYAN}phantom --profile pro --wireless${NC}   (120 FPS / Apple Display Silhouette)"
echo -e "     ${CYAN}phantom --virtual-session${NC}          (Independent locked-screen session)"
echo -e "     ${CYAN}phantom doctor${NC}                     (System & hardware verification)\n"
