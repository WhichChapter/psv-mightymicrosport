#include <errno.h>
#include <stddef.h>
#include <reent.h>
#include <psp2/kernel/rng.h>

// Newlib routes getentropy() through this reentrant hook.
int _getentropy_r(struct _reent *reent, void *buffer, size_t length) {
    if (!buffer || length > 256) {
        if (reent) reent->_errno = EINVAL;
        return -1;
    }
    int result = sceKernelGetRandomNumber(buffer, (SceSize)length);
    if (result < 0) {
        if (reent) reent->_errno = EIO;
        return -1;
    }
    return 0;
}
