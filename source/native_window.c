#include "native_window.h"

// UnityPlayerActivity supplies an Android Surface. FalsoNDK's Vita window
// shim represents that surface with a fixed 960x544 native window.
ANativeWindow *ANativeWindow_fromSurface(JNIEnv *env, jobject surface) {
    (void)env;
    (void)surface;
    return ANativeWindow_create();
}

void ANativeWindow_acquire(ANativeWindow *window) {
    (void)window;
}

void ANativeWindow_release(ANativeWindow *window) {
    // Keep the single Vita-backed window alive for Unity's EGL lifetime.
    (void)window;
}
