#!/usr/bin/env python3
"""
JAR Optimization & Hardening Utility
This script randomizes JAR entry order and injects non-executable 
decoy metadata to protect against automated bytecode analysis.
"""

import zipfile
import random
import os
import sys
import struct

def create_metadata_entry(entry_name):
    """
    Creates a non-executable class structure used for metadata protection.
    """
    name_bytes = entry_name.encode('utf-8')
    obj_bytes = b'java/lang/Object'

    # Build constant pool
    cp = bytearray()
    cp_count = 5 

    # #1: CONSTANT_Class -> #2
    cp += b'\x07' + struct.pack('>H', 2)
    # #2: CONSTANT_Utf8
    cp += b'\x01' + struct.pack('>H', len(name_bytes)) + name_bytes
    # #3: CONSTANT_Class -> #4
    cp += b'\x07' + struct.pack('>H', 4)
    # #4: CONSTANT_Utf8
    cp += b'\x01' + struct.pack('>H', len(obj_bytes)) + obj_bytes

    data = bytearray()
    data += b'\xCA\xFE\xBA\xBE'              # magic
    data += struct.pack('>HH', 0, 65)         # version
    data += struct.pack('>H', cp_count)       # cp count
    data += cp
    data += struct.pack('>H', 0x0020)         # flags
    data += struct.pack('>H', 1)              # this
    data += struct.pack('>H', 3)              # super
    data += struct.pack('>H', 0)              # interfaces
    data += struct.pack('>H', 0)              # fields
    data += struct.pack('>H', 0)              # methods
    data += struct.pack('>H', 0)              # attributes
    return bytes(data)

def harden_jar(input_path, output_path):
    """
    Processes the JAR: shuffles entries, strips metadata, and adds protection entries.
    """
    entries = []

    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return

    with zipfile.ZipFile(input_path, 'r') as zin:
        for info in zin.infolist():
            data = zin.read(info.filename)
            entries.append((info.filename, data))

    plugin_files = []
    class_files = []
    other_files = []

    for name, data in entries:
        if name in ('plugin.yml', 'config.yml', 'META-INF/MANIFEST.MF'):
            plugin_files.append((name, data))
        elif name.endswith('.class'):
            class_files.append((name, data))
        else:
            other_files.append((name, data))

    # Add protective metadata entries
    protection_keys = ['a', 'b', 'c', 'I', 'l', 'O', 'o']
    protection_entries = []
    for key in protection_keys:
        name = f'{key}.class'
        if name not in [n for n, _ in class_files]:
            protection_entries.append((name, create_metadata_entry(key)))

    all_classes = class_files + protection_entries
    random.shuffle(all_classes)

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zout:
        # Write manifest
        for name, data in plugin_files:
            if name == 'META-INF/MANIFEST.MF':
                zout.writestr(name, data)

        # Write classes (shuffled)
        for name, data in all_classes:
            zout.writestr(name, data)

        # Write config
        for name, data in plugin_files:
            if name != 'META-INF/MANIFEST.MF':
                zout.writestr(name, data)

        # Write resources
        for name, data in other_files:
            zout.writestr(name, data)

    print(f"  - Optimized {len(all_classes)} entries")
    print(f"  - Injected {len(protection_entries)} protection layers")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(1)
    harden_jar(sys.argv[1], sys.argv[2])
