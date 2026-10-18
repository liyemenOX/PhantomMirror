#!/usr/bin/env bash
# ==============================================================================
# PhantomMirror Server Daemon Build Script
# Compiles Java sources, dexes with D8, and packages classes.dex into JAR
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================="
echo "⚡ Building PhantomMirror Android Daemon (DEX + JAR)..."
echo "=================================================="

BUILD_DIR="build"
CLASSES_DIR="$BUILD_DIR/classes"
R8_JAR="$SCRIPT_DIR/tools/r8.jar"

# Download standalone D8 compiler if not present
if [ ! -f "$R8_JAR" ]; then
    echo "[+] Fetching official Google D8 compiler..."
    mkdir -p tools
    curl -L -o "$R8_JAR" https://storage.googleapis.com/r8-releases/raw/8.2.47/r8lib.jar
fi

rm -rf "$BUILD_DIR"
mkdir -p "$CLASSES_DIR"

# 1. Compile Java sources targeting Java 8/11 compatibility
echo "[+] Compiling Java source files..."
javac --release 8 -d "$CLASSES_DIR" $(find src/main/java -name "*.java")

# 2. Convert .class files to Android classes.dex using D8
echo "[+] Dexing bytecode with Google D8 (targeting Android API 26+)..."
CLASS_FILES=$(find "$CLASSES_DIR" -name "*.class")
java -cp "$R8_JAR" com.android.tools.r8.D8 --release --min-api 26 --output "$BUILD_DIR" $CLASS_FILES

# 3. Package classes.dex into phantom-server.jar for app_process
echo "[+] Packaging classes.dex into phantom-server.jar..."
jar cfe "$BUILD_DIR/phantom-server.jar" com.phantom.mirror.PhantomServer -C "$BUILD_DIR" classes.dex

echo "=================================================="
echo "[✓] Build successful! Android ART Executable: $BUILD_DIR/phantom-server.jar"
echo "=================================================="
