#!/usr/bin/env bash
# ==============================================================================
# PhantomMirror Server Daemon Build Script
# Compiles and packages phantom-server.jar with zero external dependencies
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================="
echo "[*] Building PhantomMirror Server Daemon (JAR)..."
echo "=================================================="

BUILD_DIR="build"
CLASSES_DIR="$BUILD_DIR/classes"

rm -rf "$BUILD_DIR"
mkdir -p "$CLASSES_DIR"

# 1. Compile Java sources
echo "[+] Compiling Java source files..."
javac -d "$CLASSES_DIR" $(find src/main/java -name "*.java")

# 2. Package into executable JAR
echo "[+] Packaging phantom-server.jar..."
jar cfe "$BUILD_DIR/phantom-server.jar" com.phantom.mirror.PhantomServer -C "$CLASSES_DIR" .

echo "=================================================="
echo "[✓] Build successful! Artifact: $BUILD_DIR/phantom-server.jar"
echo "=================================================="
