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
anchor = 'add_executable(${CMAKE_PROJECT_NAME} ${SOURCES})'
if anchor in text and 'list(APPEND SOURCES source/native_window.c)' not in text:
    text = text.replace(anchor, 'if (NDK_PORT)\n  list(APPEND SOURCES source/native_window.c)\nendif()\n\n' + anchor, 1)
if "source/egl_extra.c" not in text:
    text = text.replace(anchor, "list(APPEND SOURCES source/egl_extra.c)\n" + anchor, 1)
if "max-page-size=0x200000" not in text:
    text = text.replace(anchor, anchor + '''
target_link_options(${CMAKE_PROJECT_NAME} PRIVATE
    "-Wl,-z,max-page-size=0x10000"
    "-Wl,-z,common-page-size=0x10000"
    "-Wl,--section-start=.init_array=0x81400000"
)
''', 1)
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

text = text.replace('''    so_patch();
    l_success("SO patched.");''', '''    l_info("CHECKPOINT: entering so_patch");
    so_patch();
    l_info("CHECKPOINT: so_patch returned");
    l_success("SO patched.");''', 1)

text = text.replace('''    so_initialize(&so_mod);
    mm_initialize_dependencies();
    l_success("Android shared objects initialized.");''', '''    l_info("CHECKPOINT: entering libmain so_initialize");
    so_initialize(&so_mod);
    l_info("CHECKPOINT: libmain so_initialize returned");
    l_info("CHECKPOINT: entering dependency initialization");
    mm_initialize_dependencies();
    l_info("CHECKPOINT: dependency initialization returned");
    l_success("Android shared objects initialized.");''', 1)

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

# FalsoNDK's current softfp build omits errno's C++ header in its shared utility header.
fndk_utils = vendor / "lib" / "falso_ndk" / "FalsoNDK_Utils.h"
fndk_text = fndk_utils.read_text(encoding="utf-8")
if "#include <cerrno>" not in fndk_text:
    fndk_text = fndk_text.replace("#pragma once", "#pragma once\n#ifdef __cplusplus\n#include <cerrno>\n#else\n#include <errno.h>\n#endif", 1)
fndk_utils.write_text(fndk_text, encoding="utf-8")

# Add the Android Surface conversion functions missing from the upstream shim.
# Persist so_util's unresolved-import diagnostics. Its upstream critical
# logger only calls sceClibPrintf, so the Vita-side log misses the exact
# Android symbol that causes reloc_err() to abort at runtime.
so_util = vendor / "lib" / "so_util" / "so_util.c"
so_util_text = so_util.read_text(encoding="utf-8")
if "mm_so_util_log(" not in so_util_text:
    so_util_text = so_util_text.replace(
        '#include <string.h>',
        '#include <string.h>\n#include <stdarg.h>\n#include <psp2/io/fcntl.h>', 1)
    logger_impl = """
static void mm_so_util_log(const char *fmt, ...) {
    char buffer[768];
    va_list args;
    va_start(args, fmt);
    vsnprintf(buffer, sizeof(buffer), fmt, args);
    va_end(args);

    sceClibPrintf("%s", buffer);
    SceUID fd = sceIoOpen("ux0:data/mightymicros.log",
        SCE_O_WRONLY | SCE_O_CREAT | SCE_O_APPEND, 0777);
    if (fd >= 0) {
        sceIoWrite(fd, buffer, strlen(buffer));
        sceIoClose(fd);
    }
}

"""
    macro = '#define SO_UTIL_LOG_CRITICAL sceClibPrintf'
    if macro not in so_util_text:
        raise SystemExit("Could not find so_util critical logger macro")
    so_util_text = so_util_text.replace(macro, logger_impl + '#define SO_UTIL_LOG_CRITICAL mm_so_util_log', 1)
    so_util.write_text(so_util_text, encoding="utf-8")

dynlib = vendor / "source" / "dynlib.c"
dynlib_text = dynlib.read_text(encoding="utf-8")

# Android's bionic exports strsep, but the upstream Vita loader's import table
# does not. Provide the POSIX/BSD-compatible implementation locally so ELF
# relocation can resolve the symbol instead of leaving a null import.
# Add a Vita-specific getauxval implementation for Android CPU feature probes.
if "static unsigned long mm_getauxval(" not in dynlib_text:
    aux_impl = """static unsigned long mm_getauxval(unsigned long type) {
    switch (type) {
        case 6:  /* AT_PAGESZ */ return 4096;
        case 16: /* AT_HWCAP: Cortex-A9 ARMv7, VFPv3-D32 and NEON */
            return (1UL << 4)  | /* FAST_MULT */
                   (1UL << 6)  | /* VFP */
                   (1UL << 7)  | /* EDSP */
                   (1UL << 11) | /* THUMBEE */
                   (1UL << 12) | /* NEON */
                   (1UL << 13) | /* VFPv3 */
                   (1UL << 15) | /* TLS */
                   (1UL << 19);  /* VFPD32 */
        case 17: /* AT_CLKTCK */ return 100;
        case 23: /* AT_SECURE */ return 0;
        case 26: /* AT_HWCAP2 */ return 0;
        default: return 0;
    }
}

"""
    table_anchor = "so_default_dynlib default_dynlib[] = {"
    if table_anchor not in dynlib_text:
        raise SystemExit("Could not add getauxval: dynlib table anchor missing")
    dynlib_text = dynlib_text.replace(table_anchor, aux_impl + table_anchor, 1)

if '{ "getauxval", (uintptr_t)&mm_getauxval }' not in dynlib_text:
    syscalls_anchor = '        { "getpagesize", (uintptr_t)&getpagesize },'
    if syscalls_anchor not in dynlib_text:
        raise SystemExit("Could not register getauxval: syscall table anchor missing")
    dynlib_text = dynlib_text.replace(syscalls_anchor,
        '        { "getauxval", (uintptr_t)&mm_getauxval },\n' + syscalls_anchor, 1)

if "static char *mm_strsep(" not in dynlib_text:
    strsep_impl = """static char *mm_strsep(char **stringp, const char *delim) {
    if (!stringp || !*stringp) return NULL;

    char *start = *stringp;
    char *cursor = start;
    while (*cursor) {
        for (const char *d = delim; *d; ++d) {
            if (*cursor == *d) {
                *cursor = '\\0';
                *stringp = cursor + 1;
                return start;
            }
        }
        ++cursor;
    }

    *stringp = NULL;
    return start;
}

"""
    table_anchor = "so_default_dynlib default_dynlib[] = {"
    if table_anchor not in dynlib_text:
        raise SystemExit("Could not add strsep: upstream dynlib table anchor missing")
    dynlib_text = dynlib_text.replace(table_anchor, strsep_impl + table_anchor, 1)

if '{ "strsep", (uintptr_t)&mm_strsep }' not in dynlib_text:
    strings_anchor = "        // Strings\n"
    if strings_anchor not in dynlib_text:
        raise SystemExit("Could not add strsep import: upstream Strings table anchor missing")
    dynlib_text = dynlib_text.replace(
        strings_anchor,
        strings_anchor + '        { "strsep", (uintptr_t)&mm_strsep },\n',
        1)
if '#include "multiso.h"' not in dynlib_text:
    dynlib_text = dynlib_text.replace(
        '#include "utils/logger.h"',
        '#include "utils/logger.h"\n#include "multiso.h"', 1)

old_dlsym = """void *dlsym_soloader(void * handle, const char * symbol) {
    for (int i = 0; i < sizeof(default_dynlib) / sizeof(default_dynlib[0]); i++) {
        if (strcmp(symbol, default_dynlib[i].symbol) == 0) {
            return &default_dynlib[i].func;
        }
    }

    l_error("dlsym: Unknown symbol \\"%s\\".", symbol);
    return NULL;
}"""
new_dlsym = """void *dlsym_soloader(void * handle, const char * symbol) {
    (void)handle;

    /* Resolve exports from libmain.so, libunity.so and libil2cpp.so first.
       Unity's libil2cpp API is loaded dynamically and is not in DT_NEEDED. */
    uintptr_t loaded_symbol = mm_find_loaded_symbol(symbol);
    if (loaded_symbol) return (void *)loaded_symbol;

    /* POSIX dlsym returns the symbol address, not the address of the table slot. */
    for (int i = 0; i < sizeof(default_dynlib) / sizeof(default_dynlib[0]); i++) {
        if (strcmp(symbol, default_dynlib[i].symbol) == 0) {
            return (void *)default_dynlib[i].func;
        }
    }

    l_error("dlsym: Unknown symbol \\"%s\\".", symbol);
    return NULL;
}"""
if "mm_find_loaded_symbol(symbol)" not in dynlib_text:
    if old_dlsym not in dynlib_text:
        raise SystemExit("Could not locate upstream dlsym_soloader implementation")
    dynlib_text = dynlib_text.replace(old_dlsym, new_dlsym, 1)

if '#include "native_window.h"' not in dynlib_text:
    dynlib_text = dynlib_text.replace('#include "reimpl/asset_manager.h"', '#include "reimpl/asset_manager.h"\n#ifdef NDK_PORT\n#include "native_window.h"\n#endif', 1)
window_anchor = '        {"ANativeWindow_getHeight", (uintptr_t)&ANativeWindow_getHeight},'
window_add = '''        {"ANativeWindow_fromSurface", (uintptr_t)&ANativeWindow_fromSurface},
        {"ANativeWindow_acquire", (uintptr_t)&ANativeWindow_acquire},
        {"ANativeWindow_release", (uintptr_t)&ANativeWindow_release},
        {"ANativeWindow_getHeight", (uintptr_t)&ANativeWindow_getHeight},'''
if '"ANativeWindow_fromSurface"' not in dynlib_text:
    if window_anchor not in dynlib_text:
        raise SystemExit("Could not add Android native-window symbols")
    dynlib_text = dynlib_text.replace(window_anchor, window_add, 1)
dynlib.write_text(dynlib_text, encoding="utf-8")

# Complete the small EGL surface-state API used by Unity 2017.
egl_header = vendor / "source" / "reimpl" / "egl.h"
egl_h = egl_header.read_text(encoding="utf-8")
if "eglCreatePbufferSurface" not in egl_h:
    egl_h = egl_h.replace(
        'EGLSurface eglCreateWindowSurface(EGLDisplay dpy, EGLConfig config, void * win,\n                                  const EGLint * attrib_list);',
        'EGLSurface eglCreateWindowSurface(EGLDisplay dpy, EGLConfig config, void * win,\n                                  const EGLint * attrib_list);\nEGLSurface eglCreatePbufferSurface(EGLDisplay dpy, EGLConfig config, const EGLint *attrib_list);\nEGLSurface eglGetCurrentSurface(EGLint readdraw);'
    )
egl_header.write_text(egl_h, encoding="utf-8")

egl_source = vendor / "source" / "reimpl" / "egl.c"
egl_c = egl_source.read_text(encoding="utf-8")
if "static EGLSurface current_surface" not in egl_c:
    egl_c = egl_c.replace('#include <stdlib.h>', '#include <stdlib.h>\n\nstatic EGLContext current_context = NULL;\nstatic EGLSurface current_surface = NULL;', 1)
egl_c = egl_c.replace(
    '''EGLBoolean eglMakeCurrent(EGLDisplay dpy, EGLSurface draw, EGLSurface read,
                          EGLContext ctx) {
    return EGL_TRUE;
}''',
    '''EGLBoolean eglMakeCurrent(EGLDisplay dpy, EGLSurface draw, EGLSurface read,
                          EGLContext ctx) {
    current_context = ctx;
    current_surface = draw;
    return EGL_TRUE;
}''', 1)
egl_c = egl_c.replace(
    '''EGLBoolean eglDestroyContext (EGLDisplay dpy, EGLContext ctx) {
    if (ctx) free(ctx);
    return EGL_TRUE;
}''',
    '''EGLBoolean eglDestroyContext (EGLDisplay dpy, EGLContext ctx) {
    if (ctx == current_context) current_context = NULL;
    if (ctx) free(ctx);
    return EGL_TRUE;
}''', 1)
egl_c = egl_c.replace(
    '''EGLBoolean eglDestroySurface (EGLDisplay dpy, EGLSurface surface) {
    if (surface) free(surface);
    return EGL_TRUE;
}''',
    '''EGLBoolean eglDestroySurface (EGLDisplay dpy, EGLSurface surface) {
    if (surface == current_surface) current_surface = NULL;
    if (surface) free(surface);
    return EGL_TRUE;
}''', 1)
egl_c = egl_c.replace(
    '''EGLContext eglGetCurrentContext (void) {
    return strdup("ctx");
}''',
    '''EGLContext eglGetCurrentContext (void) {
    return current_context;
}

EGLSurface eglGetCurrentSurface(EGLint readdraw) {
    (void)readdraw;
    return current_surface;
}

EGLSurface eglCreatePbufferSurface(EGLDisplay dpy, EGLConfig config, const EGLint *attrib_list) {
    (void)dpy; (void)config; (void)attrib_list;
    return strdup("pbuffer");
}''', 1)
egl_source.write_text(egl_c, encoding="utf-8")

if '"eglCreatePbufferSurface"' not in dynlib_text:
    dynlib_text = dynlib_text.replace(
        '        { "eglCreateContext", (uintptr_t)&eglCreateContext },',
        '        { "eglCreateContext", (uintptr_t)&eglCreateContext },\n        { "eglCreatePbufferSurface", (uintptr_t)&eglCreatePbufferSurface },', 1)
    dynlib_text = dynlib_text.replace(
        '        { "eglGetCurrentContext", (uintptr_t)&eglGetCurrentContext },',
        '        { "eglGetCurrentContext", (uintptr_t)&eglGetCurrentContext },\n        { "eglGetCurrentSurface", (uintptr_t)&eglGetCurrentSurface },', 1)
    dynlib_text = dynlib_text.replace(
        '        { "eglSwapBuffers", (uintptr_t)&eglSwapBuffers },',
        '        { "eglSwapBuffers", (uintptr_t)&eglSwapBuffers },\n        { "eglSwapInterval", (uintptr_t)&eglSwapInterval },', 1)
dynlib.write_text(dynlib_text, encoding="utf-8")


# Persist FalsoJNI warnings/errors alongside the port logger. This is essential
# because Android JNI lookups happen during startup, before the Unity loop.
fjni_logger = vendor / "lib" / "falso_jni" / "FalsoJNI_Logger.c"
fjni_log_text = fjni_logger.read_text(encoding="utf-8")
if "#include <psp2/io/fcntl.h>" not in fjni_log_text:
    fjni_log_text = fjni_log_text.replace(
        '#include <psp2/kernel/threadmgr.h>',
        '#include <psp2/kernel/threadmgr.h>\n#include <psp2/io/fcntl.h>', 1)
old_print = "    sceClibPrintf(_fjni_log_buffer_2);"
new_print = (
    "    sceClibPrintf(_fjni_log_buffer_2); \\\n"
    "    SceUID fjni_fd = sceIoOpen(\"ux0:data/mightymicros.log\", SCE_O_WRONLY | SCE_O_CREAT | SCE_O_APPEND, 0777); \\\n"
    "    if (fjni_fd >= 0) { \\\n"
    "        sceIoWrite(fjni_fd, _fjni_log_buffer_2, strlen(_fjni_log_buffer_2)); \\\n"
    "        sceIoClose(fjni_fd); \\\n"
    "    }")
if 'sceIoOpen("ux0:data/mightymicros.log"' not in fjni_log_text:
    if old_print not in fjni_log_text:
        raise SystemExit("Could not add persistent FalsoJNI diagnostics")
    fjni_log_text = fjni_log_text.replace(old_print, new_print, 1)
fjni_logger.write_text(fjni_log_text, encoding="utf-8")

# The upstream ARM kuser helper reserves 0x9A000000, but the Android
# libraries loaded by this port occupy 0x98000000..0x9AF00000. Put the
# 4 KiB helper block in the free gap before the first Android library.
patch = vendor / "source" / "patch.c"
patch_text = patch.read_text(encoding="utf-8")
patch_text = patch_text.replace("0x9A000000", "0x97000000")
patch_text = patch_text.replace("0x9A000FA0", "0x97000FA0")
patch_text = patch_text.replace("0x9A000FC0", "0x97000FC0")
if "0x9A000000" in patch_text or "0x9A000FA0" in patch_text or "0x9A000FC0" in patch_text:
    raise SystemExit("Old overlapping kuser address remains in patch.c")
patch.write_text(patch_text, encoding="utf-8")


# Unity 2017's native WWW bridge requires Java-side Thread methods on its
# com.unity3d.player.WWW wrapper. FalsoJNI's boilerplate starts with an empty
# method table, so nativeInitWWW aborts when GetMethodID("start") returns NULL.
# Register the required methods. Network work itself remains unavailable on
# Vita, but these safe stubs allow Unity's optional WWW bridge to initialise.
java_impl = vendor / "source" / "java.c"
java_text = java_impl.read_text(encoding="utf-8")
if "mm_www_thread_noop" not in java_text:
    helpers = """
/* Minimal Java WWW thread compatibility for Unity's Android JNI bootstrap. */
static void mm_www_thread_noop(jmethodID id, va_list args) {
    (void)id;
    (void)args;
}

static jboolean mm_www_thread_not_alive(jmethodID id, va_list args) {
    (void)id;
    (void)args;
    return JNI_FALSE;
}

"""
    table_anchor = "NameToMethodID nameToMethodId[] = {};"
    if table_anchor not in java_text:
        raise SystemExit("Could not patch FalsoJNI Java method table")
    java_text = java_text.replace(table_anchor, helpers + table_anchor, 1)
    java_text = java_text.replace(
        "NameToMethodID nameToMethodId[] = {};",
        """NameToMethodID nameToMethodId[] = {
    { 1, "com/unity3d/player/WWW/<init>", METHOD_TYPE_VOID },
    { 2, "start", METHOD_TYPE_VOID },
    { 3, "join", METHOD_TYPE_VOID },
    { 4, "isAlive", METHOD_TYPE_BOOLEAN },
};""", 1)
    java_text = java_text.replace(
        "MethodsBoolean methodsBoolean[] = {};",
        "MethodsBoolean methodsBoolean[] = { { 4, mm_www_thread_not_alive } };", 1)
    java_text = java_text.replace(
        "MethodsVoid methodsVoid[] = {};",
        """MethodsVoid methodsVoid[] = {
    { 1, mm_www_thread_noop },
    { 2, mm_www_thread_noop },
    { 3, mm_www_thread_noop },
};""", 1)
    if "mm_www_thread_noop" not in java_text or '{ 2, "start", METHOD_TYPE_VOID }' not in java_text:
        raise SystemExit("Unity WWW JNI compatibility patch did not apply")
    java_impl.write_text(java_text, encoding="utf-8")

# Unity's Android transport bootstrap creates a Java Runnable worker. The
# Vita port has no Android networking runtime, so register the constructor and
# run() entry point as explicit no-op compatibility methods. This lets
# TransportAndroid initialise without calling a missing JNI method ID.
if "mm_transport_thread_noop" not in java_text:
    helpers = """
/* Minimal Java TransportAndroid worker compatibility. */
static void mm_transport_thread_noop(jmethodID id, va_list args) {
    (void)id;
    (void)args;
}

"""
    table_anchor = "NameToMethodID nameToMethodId[] = {"
    if table_anchor not in java_text:
        raise SystemExit("Could not extend FalsoJNI Java method table for TransportAndroid")
    java_text = java_text.replace(table_anchor, helpers + table_anchor, 1)
    java_text = java_text.replace(
        '    { 4, "isAlive", METHOD_TYPE_BOOLEAN },',
        '    { 4, "isAlive", METHOD_TYPE_BOOLEAN },\n'
        '    { 5, "com/unity3d/player/UnityWebRequest/<init>", METHOD_TYPE_VOID },\n'
        '    { 6, "run", METHOD_TYPE_VOID },', 1)
    java_text = java_text.replace(
        '    { 3, mm_www_thread_noop },',
        '    { 3, mm_www_thread_noop },\n'
        '    { 5, mm_transport_thread_noop },\n'
        '    { 6, mm_transport_thread_noop },', 1)
    if '{ 5, "com/unity3d/player/UnityWebRequest/<init>", METHOD_TYPE_VOID }' not in java_text:
        raise SystemExit("TransportAndroid JNI method registrations did not apply")
    java_impl.write_text(java_text, encoding="utf-8")

init.write_text(text, encoding="utf-8")
print("Patched upstream loader to map libunity.so + libil2cpp.so before libmain.so.")
