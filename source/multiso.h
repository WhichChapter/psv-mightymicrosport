#ifndef MIGHTY_MICROS_MULTISO_H
#define MIGHTY_MICROS_MULTISO_H

#include <so_util/so_util.h>
#include <stdint.h>

int mm_load_dependencies(void);
uintptr_t mm_next_load_address(void);
void mm_relocate_dependencies(void);
void mm_resolve_dependencies(void);
void mm_flush_dependencies(void);
void mm_initialize_dependencies(void);
so_module *mm_unity_module(void);
uintptr_t mm_find_loaded_symbol(const char *symbol);

#endif
