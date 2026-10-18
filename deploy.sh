#!/usr/bin/env bash
# ==============================================================================
# PhantomMirror Android Deployment & Launch Utility
# Pushes the server daemon to an Android device via ADB and executes it.
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

SERVER_JAR="$SCRIPT_DIR/phantom-server/build/phantom-server.jar"
REMOTE_TMP="/data/local/tmp/phantom-server.jar"
PORT="${1:-49152}"

echo "=================================================="
echo "⚡ PhantomMirror Android Deployer"
echo "=================================================="

# Check if JAR exists, if not build it
if [ ! -f "$SERVER_JAR" ]; then
    echo "[*] JAR not found. Building phantom-server.jar..."
    ./phantom-server/build.sh
fi

# Check for ADB
if ! command -v adb &> /dev/null; then
    echo "[-] Error: 'adb' command not found in PATH."
    echo "[!] Please ensure Android SDK Platform-Tools or 'adb' is installed."
    exit 1
fi

echo "[+] Checking for connected devices..."
DEVICES=$(adb devices | grep -v "List" | grep "device" || true)

if [ -z "$DEVICES" ]; then
    echo "[-] No Android device detected via ADB."
    echo "[!] Connect your phone via USB or Wi-Fi with USB Debugging enabled."
    exit 1
fi

echo "[+] Target device ready."
echo "[+] Pushing $SERVER_JAR -> $REMOTE_TMP..."
adb push "$SERVER_JAR" "$REMOTE_TMP"

echo "[+] Starting PhantomMirror server daemon on port $PORT..."
echo "[*] Press Ctrl+C to stop the remote daemon."
echo "=================================================="

adb shell CLASSPATH="$REMOTE_TMP" app_process / com.phantom.mirror.PhantomServer "$PORT"
