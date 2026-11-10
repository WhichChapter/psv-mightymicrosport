#include "utils/init.h"
#include "utils/glutil.h"
#include "utils/logger.h"
#include "multiso.h"
#include "native_registry.h"
#include <psp2/kernel/threadmgr.h>
#include <psp2/ctrl.h>
#include <falso_jni/FalsoJNI.h>
#include <so_util/so_util.h>
#include "reimpl/controls.h"
#include <stdio.h>

int _newlib_heap_size_user = 256 * 1024 * 1024;
int sceLibcHeapSize = 4 * 1024 * 1024;
so_module so_mod;

static uintptr_t mm_method(const char *name, const char *signature) {
    return mm_find_native_method("com/unity3d/player/UnityPlayer", name, signature);
}

int main(void) {
    l_info("Mighty Micros Vita loader starting");
    soloader_init_all();

    uintptr_t main_entry = so_symbol(&so_mod, "JNI_OnLoad");
    if (!main_entry) {
        l_error("JNI_OnLoad was not exported by libmain.so");
        sceKernelExitDeleteThread(0);
        return 0;
    }
    int (*main_jni_onload)(void *) = (int (*)(void *))main_entry;
    int main_jni_version = main_jni_onload(&jvm);
    l_info("libmain JNI_OnLoad returned 0x%x", main_jni_version);

    so_module *unity = mm_unity_module();
    uintptr_t unity_entry = unity ? so_symbol(unity, "JNI_OnLoad") : 0;
    if (!unity_entry) {
        l_error("JNI_OnLoad was not exported by libunity.so");
        sceKernelExitDeleteThread(0);
        return 0;
    }
    int (*unity_jni_onload)(void *) = (int (*)(void *))unity_entry;
    int unity_jni_version = unity_jni_onload(&jvm);
    l_info("libunity JNI_OnLoad returned 0x%x", unity_jni_version);

    mm_dump_native_methods();
    gl_init();

    JNIEnv *env = &jni;
    jobject player = (jobject)0x42424242;
    jobject context = (jobject)0x69696969;
    jobject surface = (jobject)0x69696969;

    uintptr_t init_jni = mm_method("initJni", "(Landroid/content/Context;)V");
    if (init_jni) {
        ((void (*)(JNIEnv *, jobject, jobject))init_jni)(env, player, context);
        l_info("Called UnityPlayer.initJni");
    }

    uintptr_t init_www = mm_method("nativeInitWWW", "(Ljava/lang/Class;)V");
    if (init_www) {
        jclass www_class = (*env)->FindClass(env, "com/unity3d/player/WWW");
        ((void (*)(JNIEnv *, jobject, jclass))init_www)(env, player, www_class);
    }

    uintptr_t init_web = mm_method("nativeInitWebRequest", "(Ljava/lang/Class;)V");
    if (init_web) {
        jclass web_class = (*env)->FindClass(env, "com/unity3d/player/UnityWebRequest");
        ((void (*)(JNIEnv *, jobject, jclass))init_web)(env, player, web_class);
    }

    uintptr_t recreate = mm_method("nativeRecreateGfxState", "(ILandroid/view/Surface;)V");
    if (recreate) {
        ((void (*)(JNIEnv *, jobject, jint, jobject))recreate)(env, player, 0, surface);
        l_info("Requested Unity graphics-state creation");
    }

    uintptr_t resume = mm_method("nativeResume", "()V");
    if (resume) ((void (*)(JNIEnv *, jobject))resume)(env, player);

    uintptr_t focus = mm_method("nativeFocusChanged", "(Z)V");
    if (focus) ((void (*)(JNIEnv *, jobject, jboolean))focus)(env, player, JNI_TRUE);

    jboolean (*render)(JNIEnv *, jobject) =
        (jboolean (*)(JNIEnv *, jobject))mm_method("nativeRender", "()Z");
    if (!render) {
        l_error("UnityPlayer.nativeRender was not registered; stopping before render loop");
        sceKernelExitDeleteThread(0);
        return 0;
    }

    l_info("Entering Unity nativeRender loop");
    for (;;) {
        controls_poll();
        render(env, player);

        SceCtrlData pad;
        sceCtrlPeekBufferPositive(0, &pad, 1);
        if (pad.buttons & SCE_CTRL_START) break;
        sceKernelDelayThread(16666);
    }

    uintptr_t pause = mm_method("nativePause", "()Z");
    if (pause) ((jboolean (*)(JNIEnv *, jobject))pause)(env, player);
    sceKernelExitDeleteThread(0);
    return 0;
}

void controls_handler_key(int32_t keycode, ControlsAction action) {
    (void)keycode; (void)action;
}
void controls_handler_touch(int32_t id, float x, float y, ControlsAction action) {
    (void)id; (void)x; (void)y; (void)action;
}
void controls_handler_analog(ControlsStickId which, float x, float y, ControlsAction action) {
    (void)which; (void)x; (void)y; (void)action;
}
