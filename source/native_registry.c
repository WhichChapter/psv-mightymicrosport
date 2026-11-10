#include "native_registry.h"
#include "utils/logger.h"
#include <stdio.h>
#include <string.h>

#define MM_NATIVE_CAPACITY 256
#define MM_CLASS_LENGTH 128
#define MM_NAME_LENGTH 96
#define MM_SIGNATURE_LENGTH 192

typedef struct {
    char class_name[MM_CLASS_LENGTH];
    char name[MM_NAME_LENGTH];
    char signature[MM_SIGNATURE_LENGTH];
    uintptr_t function;
} mm_native_method;

static mm_native_method methods[MM_NATIVE_CAPACITY];
static unsigned int method_count = 0;

jint mm_register_natives(JNIEnv *env, jclass clazz, const JNINativeMethod *registered, jint count) {
    (void)env;
    const char *class_name = (const char *)clazz;
    if (!class_name || !registered || count < 0) return JNI_ERR;

    for (jint i = 0; i < count; ++i) {
        if (method_count >= MM_NATIVE_CAPACITY) {
            l_error("Native method registry is full");
            return JNI_ERR;
        }
        mm_native_method *entry = &methods[method_count++];
        snprintf(entry->class_name, sizeof(entry->class_name), "%s", class_name);
        snprintf(entry->name, sizeof(entry->name), "%s", registered[i].name ? registered[i].name : "");
        snprintf(entry->signature, sizeof(entry->signature), "%s", registered[i].signature ? registered[i].signature : "");
        entry->function = (uintptr_t)registered[i].fnPtr;
        l_info("JNI native registered: %s.%s %s @ 0x%08x",
               entry->class_name, entry->name, entry->signature, (unsigned int)entry->function);
    }
    return JNI_OK;
}

uintptr_t mm_find_native_method(const char *class_name, const char *method_name, const char *signature) {
    for (unsigned int i = 0; i < method_count; ++i) {
        if (strcmp(methods[i].class_name, class_name) == 0 &&
            strcmp(methods[i].name, method_name) == 0 &&
            (!signature || strcmp(methods[i].signature, signature) == 0)) {
            return methods[i].function;
        }
    }
    l_warn("Native method not registered: %s.%s %s",
           class_name, method_name, signature ? signature : "(any signature)");
    return 0;
}

void mm_dump_native_methods(void) {
    l_info("Captured %u Android native methods", method_count);
    for (unsigned int i = 0; i < method_count; ++i) {
        l_info("  %s.%s %s @ 0x%08x", methods[i].class_name,
               methods[i].name, methods[i].signature, (unsigned int)methods[i].function);
    }
}
