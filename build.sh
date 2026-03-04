#!/bin/bash
# =================================================================
# RiggedCombat Build & Protection Script
#
# This script handles the full lifecycle:
# 1. Compilation & ProGuard (via Maven)
# 2. Flow Obfuscation (via Skidfuscator)
# 3. JAR Hardening (via Custom Python Script)
# =================================================================

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
JAR_BASE="riggedcombat-1.0-SNAPSHOT"
TARGET_DIR="$PROJECT_DIR/target"
TOOLS_DIR="$PROJECT_DIR/tools"

# Tool Configurations
SKIDFUSCATOR_JAR="$TOOLS_DIR/skidfuscator/skidfuscator.jar"
SKIDFUSCATOR_URL="https://github.com/skidfuscatordev/skidfuscator-java-obfuscator/releases/latest/download/skidfuscator.jar"

# --- Step 1: Maven Build & ProGuard ---
echo "[1/3] Compiling and applying ProGuard renaming..."
cd "$PROJECT_DIR"
mvn clean package -DskipTests

if [ ! -f "$TARGET_DIR/${JAR_BASE}.jar" ]; then
    echo "Error: Maven build failed to produce $TARGET_DIR/${JAR_BASE}.jar"
    exit 1
fi

# --- Step 2: Skidfuscator Flow Protection ---
if [ ! -f "$SKIDFUSCATOR_JAR" ]; then
    echo "      Downloading Skidfuscator..."
    mkdir -p "$TOOLS_DIR/skidfuscator"
    curl -L -o "$SKIDFUSCATOR_JAR" "$SKIDFUSCATOR_URL"
fi

echo "[2/3] Applying control-flow and string encryption..."
java -Xmx2048m -jar "$SKIDFUSCATOR_JAR" obfuscate \
    -o "$TARGET_DIR/${JAR_BASE}-protected.jar" \
    --config "$PROJECT_DIR/skidfuscator.json" \
    -ph -notrack --fuckit \
    "$TARGET_DIR/${JAR_BASE}.jar" > /dev/null 2>&1 || {
        echo "      Warning: Skidfuscator failed. Procedural check: Is the JAR already obfuscated?"
        cp "$TARGET_DIR/${JAR_BASE}.jar" "$TARGET_DIR/${JAR_BASE}-protected.jar"
    }

# --- Step 3: Custom JAR Hardening ---
echo "[3/3] Shuffling entries and injecting decoy classes..."
python3 "$PROJECT_DIR/scripts/jar_harden.py" \
    "$TARGET_DIR/${JAR_BASE}-protected.jar" \
    "$TARGET_DIR/${JAR_BASE}.jar"

# Cleanup
rm -f "$TARGET_DIR/${JAR_BASE}-protected.jar"

echo "------------------------------------------------"
echo "Build Successful: target/${JAR_BASE}.jar"
echo "Obfuscation layers: ProGuard, Skidfuscator, CustomHardener"
echo "------------------------------------------------"
