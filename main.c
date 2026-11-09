#include <vitasdk.h>
#include <vitaGL.h>
#include <kubridge.h>
#include <stdio.h>
#include <stdlib.h>

static int mod_unity = 0;
static int mod_il2cpp = 0;
static int mod_main = 0;

int main(int argc, char *argv[]) {
    // 1. Initialize vitaGL graphics subsystem
    vglInitExtended(0, 960, 544, 0x1000000, SCE_GXM_MULTISAMPLE_4X);

    // 2. Load Unity Engine runtime via kubridge
    mod_unity = kuBridgeLoadComponent("ux0:data/game/lib/armeabi-v7a/libunity.so");

    // 3. Load IL2CPP Game Logic
    mod_il2cpp = kuBridgeLoadComponent("ux0:data/game/lib/armeabi-v7a/libil2cpp.so");

    // 4. Load Main Entry
    mod_main = kuBridgeLoadComponent("ux0:data/game/lib/armeabi-v7a/libmain.so");

    // Main Render Loop
    while (1) {
        glClearColor(0.0f, 0.0f, 0.0f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT);
        vglSwapBuffers(GL_FALSE);
    }

    return 0;
}
