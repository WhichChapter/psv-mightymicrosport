#include "utils/init.h"
#include "utils/glutil.h"
#include "utils/logger.h"
#include <psp2/kernel/threadmgr.h>
#include <falso_jni/FalsoJNI.h>
#include <so_util/so_util.h>
#include "reimpl/controls.h"
#include <stdio.h>

int _newlib_heap_size_user = 256 * 1024 * 1024;
int sceLibcHeapSize = 4 * 1024 * 1024;
so_module so_mod;

int main(void) {
    l_info("Mighty Micros Vita loader starting");
    soloader_init_all();

    uintptr_t entry = so_symbol(&so_mod, "JNI_OnLoad");
    if (!entry) {
        l_error("JNI_OnLoad was not exported by the selected game library");
        sceKernelExitDeleteThread(0);
        return 0;
    }

    int (*JNI_OnLoad)(void *) = (int (*)(void *))entry;
    int jni_version = JNI_OnLoad(&jvm);
    l_info("JNI_OnLoad returned 0x%x", jni_version);

    gl_init();

    // Unity's Android Java Activity normally drives native render/update calls.
    // The actual Unity lifecycle is wired after the APK's exports are inspected.
    while (1) {
        controls_poll();
        gl_swap();
        sceKernelDelayThread(16666);
    }
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
