#!/usr/bin/env python3
from pathlib import Path

root = Path(__file__).resolve().parents[1]
vendor = root / "vendor" / "soloader"
cmake = vendor / "CMakeLists.txt"
init = vendor / "source" / "utils" / "init.c"

text = cmake.read_text(encoding="utf-8")
needle = "    source/main.c\n"
if "source/multiso.c" not in text:
    if needle not in text:
        raise SystemExit("Could not find source list insertion point in upstream CMakeLists.txt")
    text = text.replace(needle, needle + "    source/multiso.c\n", 1)
if "source/getentropy.c" not in text:
    text = text.replace(needle, needle + "    source/getentropy.c\n", 1)
if "source/native_registry.c" not in text:
    text = text.replace(needle, needle + "    source/native_registry.c\n", 1)
cmake.write_text(text, encoding="utf-8")

text = init.read_text(encoding="utf-8")
if '#include "multiso.h"' not in text:
    text = text.replace('#include "utils/init.h"', '#include "utils/init.h"\n#include "multiso.h"', 1)

old_load = '    if (so_file_load(&so_mod, SO_PATH, LOAD_ADDRESS) < 0) {'
new_load = '''    if (mm_load_dependencies() < 0) {
        l_fatal("Android Unity dependencies could not be loaded.");
        fatal_error("Error: could not load libunity.so and libil2cpp.so.");
    }

    if (so_file_load(&so_mod, SO_PATH, mm_next_load_address()) < 0) {'''
if old_load in text:
    text = text.replace(old_load, new_load, 1)
elif "so_file_load(&so_mod, SO_PATH, mm_next_load_address())" not in text:
    raise SystemExit("Could not patch main shared-object load call")

text = text.replace('''    settings_load();
    l_success("Settings loaded.");

    so_relocate(&so_mod);
    l_success("SO relocated.");

    resolve_imports(&so_mod);
    l_success("SO imports resolved.");''','''    so_mod.soname = "libmain.so";

    settings_load();
    l_success("Settings loaded.");

    mm_relocate_dependencies();
    so_relocate(&so_mod);
    l_success("Android shared objects relocated.");

    mm_resolve_dependencies();
    resolve_imports(&so_mod);
    l_success("Android shared-object imports resolved.");''',1)

text = text.replace('''    so_flush_caches(&so_mod);
    l_success("SO caches flushed.");

    so_initialize(&so_mod);
    l_success("SO initialized.");''','''    mm_flush_dependencies();
    so_flush_caches(&so_mod);
    l_success("Android shared-object caches flushed.");

    so_initialize(&so_mod);
    mm_initialize_dependencies();
    l_success("Android shared objects initialized.");''',1)

if "mm_load_dependencies()" not in text or "mm_initialize_dependencies()" not in text:
    raise SystemExit("Multi-library loader patch was incomplete")
fjni = vendor / "lib" / "falso_jni" / "FalsoJNI.c"
fjni_text = fjni.read_text(encoding="utf-8")
if '#include "native_registry.h"' not in fjni_text:
    fjni_text = fjni_text.replace('#include "converter.h"', '#include "converter.h"\n#include "native_registry.h"', 1)
import re
pattern = r'jint RegisterNatives\(JNIEnv\* env, jclass clazz, const JNINativeMethod\* methods, jint nMethods\) \{.*?\n\}'
replacement = '''jint RegisterNatives(JNIEnv* env, jclass clazz, const JNINativeMethod* methods, jint nMethods) {
    return mm_register_natives(env, clazz, methods, nMethods);
}'''
fjni_text, changed = re.subn(pattern, replacement, fjni_text, count=1, flags=re.S)
if changed != 1:
    raise SystemExit("Could not hook FalsoJNI RegisterNatives")
fjni.write_text(fjni_text, encoding="utf-8")

logger = vendor / "source" / "utils" / "logger.c"
logger_text = logger.read_text(encoding="utf-8")
if "#include <psp2/io/fcntl.h>" not in logger_text:
    logger_text = logger_text.replace("#include <stdatomic.h>", "#include <stdatomic.h>\n#include <string.h>\n#include <psp2/io/fcntl.h>", 1)
log_call = "    sceClibPrintf(buffer_b);"
file_log = """    sceClibPrintf(buffer_b);
    SceUID log_fd = sceIoOpen("ux0:data/mightymicros.log", SCE_O_WRONLY | SCE_O_CREAT | SCE_O_APPEND, 0777);
    if (log_fd >= 0) {
        sceIoWrite(log_fd, buffer_b, strlen(buffer_b));
        sceIoClose(log_fd);
    }"""
if "ux0:data/mightymicros.log" not in logger_text:
    if log_call not in logger_text:
        raise SystemExit("Could not add persistent Vita diagnostic log")
    logger_text = logger_text.replace(log_call, file_log, 1)
logger.write_text(logger_text, encoding="utf-8")

init.write_text(text, encoding="utf-8")
print("Patched upstream loader to map libunity.so + libil2cpp.so before libmain.so.")
