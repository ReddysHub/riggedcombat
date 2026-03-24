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
    Creates a fully valid, ASM-parseable decoy class file.
    The class extends java/lang/Object and has a proper <init> constructor
    so that ASM's ClassReader can parse it without errors.
    """
    name_bytes = entry_name.encode('utf-8')
    obj_bytes = b'java/lang/Object'
    init_name = b'<init>'
    init_desc = b'()V'
    code_attr = b'Code'

    # Constant pool entries (indices 1-10, so cp_count = 11):
    #  #1: CONSTANT_Class -> #2              (this_class)
    #  #2: CONSTANT_Utf8  entry_name
    #  #3: CONSTANT_Class -> #4              (super_class = java/lang/Object)
    #  #4: CONSTANT_Utf8  "java/lang/Object"
    #  #5: CONSTANT_Utf8  "<init>"
    #  #6: CONSTANT_Utf8  "()V"
    #  #7: CONSTANT_Utf8  "Code"
    #  #8: CONSTANT_NameAndType -> #5, #6
    #  #9: CONSTANT_Methodref -> #3, #8      (java/lang/Object.<init>:()V)
    # #10: CONSTANT_Utf8  "SourceFile"       (optional but keeps ASM happy)
    cp = bytearray()
    cp_count = 11

    # #1 CONSTANT_Class -> #2
    cp += b'\x07' + struct.pack('>H', 2)
    # #2 CONSTANT_Utf8
    cp += b'\x01' + struct.pack('>H', len(name_bytes)) + name_bytes
    # #3 CONSTANT_Class -> #4
    cp += b'\x07' + struct.pack('>H', 4)
    # #4 CONSTANT_Utf8
    cp += b'\x01' + struct.pack('>H', len(obj_bytes)) + obj_bytes
    # #5 CONSTANT_Utf8 "<init>"
    cp += b'\x01' + struct.pack('>H', len(init_name)) + init_name
    # #6 CONSTANT_Utf8 "()V"
    cp += b'\x01' + struct.pack('>H', len(init_desc)) + init_desc
    # #7 CONSTANT_Utf8 "Code"
    cp += b'\x01' + struct.pack('>H', len(code_attr)) + code_attr
    # #8 CONSTANT_NameAndType -> name=#5, descriptor=#6
    cp += b'\x0c' + struct.pack('>HH', 5, 6)
    # #9 CONSTANT_Methodref -> class=#3, nameAndType=#8
    cp += b'\x0a' + struct.pack('>HH', 3, 8)
    # #10 CONSTANT_Utf8 "SourceFile"
    cp += b'\x01' + struct.pack('>H', 10) + b'SourceFile'

    # Build the Code attribute for <init>:
    #   aload_0; invokespecial #9; return
    bytecode = bytearray()
    bytecode += b'\x2a'                              # aload_0
    bytecode += b'\xb7' + struct.pack('>H', 9)       # invokespecial #9
    bytecode += b'\xb1'                              # return

    # Code attribute structure:
    #   u2 max_stack = 1
    #   u2 max_locals = 1
    #   u4 code_length
    #   u1[] code
    #   u2 exception_table_length = 0
    #   u2 attributes_count = 0
    code_body = bytearray()
    code_body += struct.pack('>H', 1)                # max_stack
    code_body += struct.pack('>H', 1)                # max_locals
    code_body += struct.pack('>I', len(bytecode))    # code_length
    code_body += bytecode
    code_body += struct.pack('>H', 0)                # exception_table_length
    code_body += struct.pack('>H', 0)                # attributes_count

    # Method: <init>()V with Code attribute
    method = bytearray()
    method += struct.pack('>H', 0x0001)              # access_flags: ACC_PUBLIC
    method += struct.pack('>H', 5)                   # name_index -> "<init>"
    method += struct.pack('>H', 6)                   # descriptor_index -> "()V"
    method += struct.pack('>H', 1)                   # attributes_count = 1
    # Code attribute
    method += struct.pack('>H', 7)                   # attribute_name_index -> "Code"
    method += struct.pack('>I', len(code_body))      # attribute_length
    method += code_body

    # Assemble the full class file
    data = bytearray()
    data += b'\xCA\xFE\xBA\xBE'                     # magic
    data += struct.pack('>HH', 0, 61)               # version: Java 17
    data += struct.pack('>H', cp_count)              # constant_pool_count
    data += cp
    data += struct.pack('>H', 0x0021)               # access_flags: ACC_PUBLIC | ACC_SUPER
    data += struct.pack('>H', 1)                     # this_class -> #1
    data += struct.pack('>H', 3)                     # super_class -> #3
    data += struct.pack('>H', 0)                     # interfaces_count
    data += struct.pack('>H', 0)                     # fields_count
    data += struct.pack('>H', 1)                     # methods_count = 1
    data += method
    data += struct.pack('>H', 0)                     # class attributes_count
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
