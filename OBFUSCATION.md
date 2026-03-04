# Obfuscation Disclosure - RiggedCombat

To the Modrinth Content Moderation Team:

As requested, this document outlines the obfuscation process used for **RiggedCombat**. We appreciate the work you do to keep the community safe and are happy to provide full transparency regarding our protection pipeline.

## Why Obfuscation is Used
The obfuscation applied to this project is intended solely to protect the intellectual property of the plugin's logic from being easily reverse-engineered or stolen. It is **not** used to hide malicious behavior. The clean source code is provided here for your review and audit.

## Protection Pipeline

The final JAR is processed through three distinct layers:

### 1. ProGuard (Structural Renaming)
*   **Stage:** Runs during the Maven `package` phase.
*   **Config:** `proguard.conf`
*   **Actions:**
    *   Renames all internal classes, methods, and fields to short, non-descriptive names (e.g., `a`, `b`).
    *   Flattens the package hierarchy to the root.
    *   Strips all Local Variable Tables and Source File attributes (line numbers, variable names).

### 2. Skidfuscator (Logic Obfuscation)
*   **Stage:** Post-compile processing.
*   **Actions:**
    *   **Control Flow Gen3:** Transforms linear Java logic into complex, non-deterministic bytecode jumps.
    *   **String Encryption:** Encrypts all constant strings (messages, config keys) using AES, decrypting them only at runtime.
    *   **Number Obfuscation:** Replaces static integers with complex arithmetic expressions.

### 3. JAR Hardening (Packaging Protection)
*   **Stage:** Final assembly (`scripts/jar_harden.py`).
*   **Actions:**
    *   **Entry Shuffling:** Randomizes the order of files within the JAR to disrupt sequential scanners.
    *   **Decoy Injection:** Injects multiple "junk" class files with invalid bytecode headers that cause many common decompilers (like JD-GUI or older Luyten) to crash or hang while remaining perfectly safe for the JVM to ignore.
    *   **Metadata Stripping:** Removes all ZIP-level comments and extra metadata.

## Build Reproducibility
You can verify the integrity of the plugin by building it yourself:
1. Ensure Java 21+ and Maven are installed.
2. Run `./build.sh`.
3. The resulting `target/riggedcombat-1.0-SNAPSHOT.jar` will be the exact obfuscated version submitted to Modrinth.
