#include <vitasdk.h>
#include <vitaGL.h>
#include <stdio.h>
#include <string.h>

#define GAME_ROOT "ux0:app/MTHM00001/data/mightymicros"
#define UNITY_SO  GAME_ROOT "/lib/armeabi-v7a/libunity.so"
#define IL2CPP_SO GAME_ROOT "/lib/armeabi-v7a/libil2cpp.so"
#define MAIN_SO   GAME_ROOT "/lib/armeabi-v7a/libmain.so"

static int file_exists(const char *path) {
    SceIoStat st;
    memset(&st, 0, sizeof(st));
    return sceIoGetstat(path, &st) >= 0;
}

int main(void) {
    int payload_ok = file_exists(UNITY_SO) &&
                     file_exists(IL2CPP_SO) &&
                     file_exists(MAIN_SO);

    printf("LEGO DC Mighty Micros - PS Vita
");
    printf("Payload check: %s\n", payload_ok ? "OK" : "MISSING");
    printf("Unity Android runtime is not started by this diagnostic build.\n");

    vglInit(0);
    glViewport(0, 0, 960, 544);
    glClearColor(payload_ok ? 0.02f : 0.18f, payload_ok ? 0.18f : 0.02f, 0.02f, 1.0f);

    for (;;) {
        SceCtrlData pad;
        sceCtrlPeekBufferPositive(0, &pad, 1);
        glClear(GL_COLOR_BUFFER_BIT);
        vglSwapBuffers(GL_FALSE);
        if (pad.buttons & SCE_CTRL_START) break;
        sceKernelDelayThread(16666);
    }

    vglExit();
    sceKernelExitProcess(0);
    return 0;
}
