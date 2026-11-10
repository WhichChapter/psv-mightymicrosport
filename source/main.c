#include "utils/init.h"
#include "utils/glutil.h"
#include "utils/logger.h"
#include "multiso.h"
#include "native_registry.h"
#include <psp2/kernel/threadmgr.h>
#include <psp2/ctrl.h>
#include <falso_jni/FalsoJNI.h>
#include <so_util/so_util.h>
#include <stdio.h>

int _newlib_heap_size_user = 256 * 1024 * 1024;
int sceLibcHeapSize = 4 * 1024 * 1024;
so_module so_mod;

static jobject unity_player = (jobject)0x42424242;
static jobject android_context = (jobject)0x69696969;
static jobject android_surface = (jobject)0x69696969;

typedef void (*unity_void_method)(JNIEnv *, jobject);
typedef void (*unity_surface_method)(JNIEnv *, jobject, jint, jobject);
typedef void (*unity_focus_method)(JNIEnv *, jobject, jboolean);
typedef jboolean (*unity_render_method)(JNIEnv *, jobject);

static unity_surface_method native_recreate_gfx_state;
static unity_void_method native_resume;
static unity_void_method native_done;
static unity_focus_method native_focus_changed;
static unity_render_method native_render;
static jboolean (*native_pause)(JNIEnv *, jobject);

static uintptr_t unity_method(const char *name, const char *signature) {
    return mm_find_native_method("com/unity3d/player/UnityPlayer", name, signature);
}

/*
 * Unity's Android Java wrapper starts a dedicated UnityMain thread. Keep the
 * same split here: JNI setup happens on the launcher thread, while EGL/GXM
 * setup, surface creation and frame pumping happen on UnityMain.
 */
static int unity_main_thread(SceSize args, void *argp) {
    (void)args;
    (void)argp;

    l_info("UnityMain thread entered");
    gl_init();
    l_info("vitaGL initialized on UnityMain");

    native_recreate_gfx_state(&jni, unity_player, 0, android_surface);
    l_info("UnityPlayer.nativeRecreateGfxState completed");

    if (native_resume) {
        native_resume(&jni, unity_player);
        l_info("UnityPlayer.nativeResume completed");
    }

    if (native_focus_changed) {
        native_focus_changed(&jni, unity_player, JNI_TRUE);
        l_info("UnityPlayer.nativeFocusChanged(true) completed");
    }

    l_info("Starting Unity nativeRender frame pump");
    for (;;) {
        native_render(&jni, unity_player);

        SceCtrlData pad;
        sceCtrlPeekBufferPositive(0, &pad, 1);
        if (pad.buttons & SCE_CTRL_START) {
            l_info("START pressed; leaving UnityMain frame pump");
            break;
        }

        sceKernelDelayThread(16666);
    }

    if (native_pause) {
        native_pause(&jni, unity_player);
        l_info("UnityPlayer.nativePause completed");
    }
    if (native_done) {
        native_done(&jni, unity_player);
        l_info("UnityPlayer.nativeDone completed");
    }

    return 0;
}

int main(void) {
    l_info("Mighty Micros Vita loader starting");
    soloader_init_all();

    /*
     * libmain.so exports NativeLoader.load/unload through JNI_OnLoad.
     * Its JNI_OnLoad must run before Unity's JNI_OnLoad, matching Android's
     * System.loadLibrary("main") startup sequence.
     */
    uintptr_t main_entry = so_symbol(&so_mod, "JNI_OnLoad");
    if (!main_entry) {
        l_error("JNI_OnLoad was not exported by libmain.so");
        sceKernelExitDeleteThread(0);
        return 0;
    }
    int (*main_jni_onload)(JavaVM *) = (int (*)(JavaVM *))main_entry;
    jint main_jni_version = main_jni_onload(&jvm);
    l_info("libmain JNI_OnLoad returned 0x%x", main_jni_version);
    if (main_jni_version < JNI_VERSION_1_4) {
        l_error("libmain JNI_OnLoad rejected the fake JavaVM");
        sceKernelExitDeleteThread(0);
        return 0;
    }

    so_module *unity = mm_unity_module();
    uintptr_t unity_entry = unity ? so_symbol(unity, "JNI_OnLoad") : 0;
    if (!unity_entry) {
        l_error("JNI_OnLoad was not exported by libunity.so");
        sceKernelExitDeleteThread(0);
        return 0;
    }
    int (*unity_jni_onload)(JavaVM *) = (int (*)(JavaVM *))unity_entry;
    jint unity_jni_version = unity_jni_onload(&jvm);
    l_info("libunity JNI_OnLoad returned 0x%x", unity_jni_version);
    if (unity_jni_version < JNI_VERSION_1_4) {
        l_error("libunity JNI_OnLoad rejected the fake JavaVM");
        sceKernelExitDeleteThread(0);
        return 0;
    }

    mm_dump_native_methods();

    /* UnityPlayer constructor calls initJni and WWW registration before its
       dedicated render thread is started. */
    uintptr_t init_jni = unity_method("initJni", "(Landroid/content/Context;)V");
    if (!init_jni) {
        l_error("UnityPlayer.initJni(Context) was not registered");
        sceKernelExitDeleteThread(0);
        return 0;
    }
    ((void (*)(JNIEnv *, jobject, jobject))init_jni)(&jni, unity_player, android_context);
    l_info("UnityPlayer.initJni completed");

    uintptr_t init_www = unity_method("nativeInitWWW", "(Ljava/lang/Class;)V");
    if (init_www) {
        jclass www_class = jni->FindClass(&jni, "com/unity3d/player/WWW");
        ((void (*)(JNIEnv *, jobject, jclass))init_www)(&jni, unity_player, www_class);
        l_info("UnityPlayer.nativeInitWWW completed");
    }

    uintptr_t init_web = unity_method("nativeInitWebRequest", "(Ljava/lang/Class;)V");
    if (init_web) {
        jclass web_class = (*(&jni))->FindClass(&jni, "com/unity3d/player/UnityWebRequest");
        ((void (*)(JNIEnv *, jobject, jclass))init_web)(&jni, unity_player, web_class);
        l_info("UnityPlayer.nativeInitWebRequest completed");
    }

    native_recreate_gfx_state = (unity_surface_method)unity_method(
        "nativeRecreateGfxState", "(ILandroid/view/Surface;)V");
    native_resume = (unity_void_method)unity_method("nativeResume", "()V");
    native_focus_changed = (unity_focus_method)unity_method("nativeFocusChanged", "(Z)V");
    native_render = (unity_render_method)unity_method("nativeRender", "()Z");
    native_pause = (jboolean (*)(JNIEnv *, jobject))unity_method("nativePause", "()Z");
    native_done = (unity_void_method)unity_method("nativeDone", "()V");

    if (!native_recreate_gfx_state || !native_render) {
        l_error("Required Unity lifecycle natives are missing; refusing unsafe render startup");
        sceKernelExitDeleteThread(0);
        return 0;
    }

    SceUID thread = sceKernelCreateThread(
        "UnityMain", unity_main_thread, 0x10000100, 4 * 1024 * 1024, 0, 0, NULL);
    if (thread < 0) {
        l_error("Could not create UnityMain thread: 0x%x", thread);
        sceKernelExitDeleteThread(0);
        return 0;
    }

    int start_result = sceKernelStartThread(thread, 0, NULL);
    if (start_result < 0) {
        l_error("Could not start UnityMain thread: 0x%x", start_result);
        sceKernelDeleteThread(thread);
        sceKernelExitDeleteThread(0);
        return 0;
    }

    l_info("UnityMain started; waiting for it to exit");
    int thread_status = 0;
    sceKernelWaitThreadEnd(thread, &thread_status, NULL);
    l_info("UnityMain exited with status %d", thread_status);
    sceKernelDeleteThread(thread);
    sceKernelExitProcess(0);
    return 0;
}
