#include <vitasdk.h>
#include <vitaGL.h>
#include <stdio.h>
#include <stdlib.h>

// Handle for kubridge dynamic library loading
static Pluginid so_mod = 0;

int main(int argc, char *argv[]) {
    // 1. Initialize vitaGL graphics subsystem (960x544 resolution)
    vglInitExtended(0, 960, 544, 0x1000000, SCE_GXM_MULTISAMPLE_4X);

    // 2. Load Android dynamic shared library into Vita RAM via kubridge
    // Change path to match where assets are stored on the Vita
    so_mod = kuBridgeLoadComponent("ux0:data/game/libgame.so");
    
    if (so_mod < 0) {
        // Verification: If loading fails, loop cleanly
        while (1) {
            vglSwapBuffers(GL_FALSE);
        }
        return -1;
    }

    // 3. Main Render / Event Loop
    while (1) {
        // Read Vita physical input controls
        SceCtrlData pad;
        sceCtrlPeekBufferPositive(0, &pad, 1);

        // Clear screen buffer
        glClearColor(0.0f, 0.0f, 0.0f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT);

        // Swap render buffers to display frame
        vglSwapBuffers(GL_FALSE);
    }

    return 0;
}
