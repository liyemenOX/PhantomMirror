#!/usr/bin/env bash
# ==============================================================================
# PhantomMirror Desktop Client Launcher
# Starts the ADB Real-Time Stream Bridge and the Web UI simultaneously.
# ==============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================="
echo "⚡ Starting PhantomMirror Desktop & Stream Bridge..."
echo "=================================================="

# Start ADB Stream Bridge
node stream-bridge.js &
BRIDGE_PID=$!

# Start Vite Development Server
npm run dev &
VITE_PID=$!

trap "echo '[*] Shutting down...'; kill $BRIDGE_PID $VITE_PID 2>/dev/null" SIGINT SIGTERM EXIT
wait
