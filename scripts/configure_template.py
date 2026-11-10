#!/usr/bin/env python3
import re, sys
from pathlib import Path

cmake = Path(sys.argv[1])
entry = sys.argv[2]
text = cmake.read_text(encoding="utf-8")
replacements = {
    r'^set\(VITA_APP_NAME ".*?"\)$': 'set(VITA_APP_NAME "LEGO DC Mighty Micros")',
    r'^set\(VITA_TITLEID ".*?"\)$': 'set(VITA_TITLEID "MTHM00001")',
    r'^set\(VITA_VPKNAME ".*?"\)$': 'set(VITA_VPKNAME "mighty_micros")',
    r'^set\(DATA_PATH ".*?"\)': 'set(DATA_PATH "ux0:data/mightymicros/")',
    r'^set\(SO_PATH ".*?"\)': f'set(SO_PATH "ux0:data/mightymicros/lib/armeabi-v7a/{entry}")',
}
for pattern, replacement in replacements.items():
    text, count = re.subn(pattern, replacement, text, count=1, flags=re.M)
    if count != 1:
        raise SystemExit(f"Expected exactly one CMake setting matching {pattern}; found {count}")
cmake.write_text(text, encoding="utf-8")
print(f"Configured loader: {entry}")
