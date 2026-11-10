#ifndef MIGHTY_MICROS_NATIVE_WINDOW_H
#define MIGHTY_MICROS_NATIVE_WINDOW_H

#include <falso_jni/FalsoJNI.h>
#include <falso_ndk/FalsoNDK.h>

#ifdef __cplusplus
extern "C" {
#endif

ANativeWindow *ANativeWindow_fromSurface(JNIEnv *env, jobject surface);
void ANativeWindow_acquire(ANativeWindow *window);
void ANativeWindow_release(ANativeWindow *window);

#ifdef __cplusplus
}
#endif

#endif
