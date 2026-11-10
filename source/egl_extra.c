#include "reimpl/egl.h"

// Unity 2017 imports this EGL entry point. The VitaGL backend does not expose
// pbuffer creation, so report it as unsupported until an off-screen surface
// implementation is available.
EGLSurface eglCreatePbufferSurface(EGLDisplay display, EGLConfig config, const EGLint *attributes) {
    (void)display;
    (void)config;
    (void)attributes;
    return NULL;
}
