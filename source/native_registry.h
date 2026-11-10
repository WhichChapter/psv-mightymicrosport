#ifndef MIGHTY_MICROS_NATIVE_REGISTRY_H
#define MIGHTY_MICROS_NATIVE_REGISTRY_H

#include <stdint.h>
#include <falso_jni/FalsoJNI.h>

jint mm_register_natives(JNIEnv *env, jclass clazz, const JNINativeMethod *methods, jint count);
uintptr_t mm_find_native_method(const char *class_name, const char *method_name, const char *signature);
void mm_dump_native_methods(void);

#endif
