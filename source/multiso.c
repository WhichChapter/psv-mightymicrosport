#include "multiso.h"
#include "utils/init.h"
#include "utils/logger.h"

#define MM_DEP_COUNT 2
#define MM_FIRST_LOAD_ADDRESS ((uintptr_t)0x98000000)
#define MM_ADDRESS_ALIGNMENT ((uintptr_t)0x00100000)

static so_module mm_dependencies[MM_DEP_COUNT];
static uintptr_t mm_next_address = MM_FIRST_LOAD_ADDRESS;
static unsigned int mm_loaded_count = 0;

int mm_load_dependencies(void) {
    static const char *paths[MM_DEP_COUNT] = {
        DATA_PATH "lib/armeabi-v7a/libunity.so",
        DATA_PATH "lib/armeabi-v7a/libil2cpp.so"
    };
    static char *sonames[MM_DEP_COUNT] = {
        "libunity.so",
        "libil2cpp.so"
    };

    for (unsigned int i = 0; i < MM_DEP_COUNT; ++i) {
        int result = so_file_load(&mm_dependencies[i], paths[i], mm_next_address);
        if (result < 0) {
            l_error("Could not load Android dependency %s (0x%x)", paths[i], result);
            return result;
        }

        // Some Unity builds omit DT_SONAME. so_util's dependency resolver
        // compares SONAME strings, so provide the known APK library names.
        mm_dependencies[i].soname = sonames[i];
        ++mm_loaded_count;

        uintptr_t end = mm_dependencies[i].text_base + mm_dependencies[i].text_size;
        for (unsigned int j = 0; j < mm_dependencies[i].n_data; ++j) {
            uintptr_t data_end = mm_dependencies[i].data_base[j] + mm_dependencies[i].data_size[j];
            if (data_end > end) end = data_end;
        }

        uintptr_t next = (end + MM_ADDRESS_ALIGNMENT - 1) & ~(MM_ADDRESS_ALIGNMENT - 1);
        if (next <= end) next += MM_ADDRESS_ALIGNMENT;
        mm_next_address = next;
        l_info("Loaded %s at 0x%08x; next module base 0x%08x",
               sonames[i], (unsigned int)mm_dependencies[i].load_addr,
               (unsigned int)mm_next_address);
    }

    return 0;
}

uintptr_t mm_next_load_address(void) {
    return mm_next_address;
}

void mm_relocate_dependencies(void) {
    for (unsigned int i = 0; i < mm_loaded_count; ++i) {
        so_relocate(&mm_dependencies[i]);
    }
}

void mm_resolve_dependencies(void) {
    for (unsigned int i = 0; i < mm_loaded_count; ++i) {
        resolve_imports(&mm_dependencies[i]);
    }
}

void mm_flush_dependencies(void) {
    for (unsigned int i = 0; i < mm_loaded_count; ++i) {
        so_flush_caches(&mm_dependencies[i]);
    }
}

void mm_initialize_dependencies(void) {
    for (unsigned int i = 0; i < mm_loaded_count; ++i) {
        so_initialize(&mm_dependencies[i]);
        l_info("Initialized %s", mm_dependencies[i].soname);
    }
}

so_module *mm_unity_module(void) {
    return mm_loaded_count > 0 ? &mm_dependencies[0] : 0;
}
