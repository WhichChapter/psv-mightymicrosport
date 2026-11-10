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
dynlib = vendor / "source" / "dynlib.c"
dynlib_text = dynlib.read_text(encoding="utf-8")
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

init.write_text(text, encoding="utf-8")
print("Patched upstream loader to map libunity.so + libil2cpp.so before libmain.so.")
