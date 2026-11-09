#include <vitasdk.h>
#include <vitaGL.h>
#include <stdio.h>
#include <string.h>

#define GAME_DIR "ux0:data/mightymicros/"
#define LIB_DIR  GAME_DIR "lib/armeabi-v7a/"

static FILE *log_file;

static void log_line(const char *message) {
    if (log_file) {
        fprintf(log_file, "%s\n", message);
        fflush(log_file);
    }
}

static int check_file(const char *path, const char *label) {
    FILE *file = fopen(path, "rb");
    char line[256];
    if (!file) {
        snprintf(line, sizeof(line), "MISSING: %s", label);
        log_line(line);
        return 0;
    }
    fclose(file);
    snprintf(line, sizeof(line), "FOUND: %s", label);
    log_line(line);
    return 1;
}

int main(int argc, char *argv[]) {
    int ready = 1;

    sceIoMkdir(GAME_DIR, 0777);
    log_file = fopen(GAME_DIR "loader.log", "w");
    log_line("Mighty Micros Vita loader - file/ABI diagnostic");
    log_line("This build does not yet execute Android Unity libraries.");

    ready &= check_file(LIB_DIR "libmain.so", "libmain.so");
    ready &= check_file(LIB_DIR "libunity.so", "libunity.so");
    ready &= check_file(LIB_DIR "libil2cpp.so", "libil2cpp.so");
    ready &= check_file(LIB_DIR "global-metadata.dat", "global-metadata.dat");
    ready &= check_file(GAME_DIR "assets/bin/Data/globalgamemanagers", "globalgamemanagers");

    log_line(ready ? "RESULT: required core files are present." :
                     "RESULT: one or more required files are missing.");
    log_line("See ux0:data/mightymicros/loader.log.");

    vglInitExtended(0, 960, 544, 0x1000000, SCE_GXM_MULTISAMPLE_4X);
    while (1) {
        glClearColor(0.025f, 0.025f, 0.04f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT);
        vglSwapBuffers(GL_FALSE);
    }

    return 0;
}
