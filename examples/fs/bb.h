////// AUTOGENERATED //////
#ifndef __BOX_SYS_H
#define __BOX_SYS_H
#include <stdbool.h>
#include <stdint.h>
#include <sys/types.h>

//// box imports ////

int32_t box1_add2(int32_t a0, int32_t a1);

int box1_hello(void);

int32_t box2_add2(int32_t a0, int32_t a1);

int box2_hello(void);

int32_t box3_add2(int32_t a0, int32_t a1);

int box3_hello(void);

//// box exports ////

extern int __box_close(int32_t fd);

extern int __box_open(int32_t *fd, const char *path, uint32_t flags);

extern ssize_t __box_read(int32_t fd, void *buffer, size_t size);

extern ssize_t __box_seek(int32_t fd, size_t off, uint32_t whence);

extern int __box_close(int32_t fd);

extern int __box_open(int32_t *fd, const char *path, uint32_t flags);

extern ssize_t __box_read(int32_t fd, void *buffer, size_t size);

extern ssize_t __box_seek(int32_t fd, size_t off, uint32_t whence);

extern int __box_close(int32_t fd);

extern int __box_open(int32_t *fd, const char *path, uint32_t flags);

extern ssize_t __box_read(int32_t fd, void *buffer, size_t size);

extern ssize_t __box_seek(int32_t fd, size_t off, uint32_t whence);

extern ssize_t __box_write(int32_t a0, const void *a1, size_t size);

//// box hooks ////

// Initialize box box1. Resets the box to its initial state if already
// initialized.
int __box_box1_init(void);

// Mark the box box1 as needing to be reinitialized.
int __box_box1_clobber(void);

// Initialize box box2. Resets the box to its initial state if already
// initialized.
int __box_box2_init(void);

// Mark the box box2 as needing to be reinitialized.
int __box_box2_clobber(void);

// Initialize box box3. Resets the box to its initial state if already
// initialized.
int __box_box3_init(void);

// Mark the box box3 as needing to be reinitialized.
int __box_box3_clobber(void);

// May be called by well-behaved code to terminate the box if execution can
// not continue. Notably used for asserts. Note that __box_abort may be
// skipped if the box is killed because of an illegal operation. Must not
// return.
__attribute__((noreturn))
void __box_abort(int err);

// Provides a minimal implementation of stdout to the box. The exact behavior
// depends on the superbox's implementation of __box_write. If none is
// provided, __box_write links but does nothing.
ssize_t __box_write(int32_t fd, const void *buffer, size_t size);

// Provides a minimal implementation of stdout to the box. The exact behavior
// depends on the superbox's implementation of __box_flush. If none is
// provided, __box_flush links but does nothing.
int __box_flush(int32_t fd);

//// box error codes ////
enum box_errors {
    EOK              = 0,    // No error
    EGENERAL         = 1,    // General error
    ENOENT           = 2,    // No such file or directory
    ESRCH            = 3,    // No such process
    EINTR            = 4,    // Interrupted system call
    EIO              = 5,    // I/O error
    ENXIO            = 6,    // No such device or address
    E2BIG            = 7,    // Argument list too long
    ENOEXEC          = 8,    // Exec format error
    EBADF            = 9,    // Bad file number
    ECHILD           = 10,   // No child processes
    EAGAIN           = 11,   // Try again
    ENOMEM           = 12,   // Out of memory
    EACCES           = 13,   // Permission denied
    EFAULT           = 14,   // Bad address
    EBUSY            = 16,   // Device or resource busy
    EEXIST           = 17,   // File exists
    EXDEV            = 18,   // Cross-device link
    ENODEV           = 19,   // No such device
    ENOTDIR          = 20,   // Not a directory
    EISDIR           = 21,   // Is a directory
    EINVAL           = 22,   // Invalid argument
    ENFILE           = 23,   // File table overflow
    EMFILE           = 24,   // Too many open files
    ENOTTY           = 25,   // Not a typewriter
    ETXTBSY          = 26,   // Text file busy
    EFBIG            = 27,   // File too large
    ENOSPC           = 28,   // No space left on device
    ESPIPE           = 29,   // Illegal seek
    EROFS            = 30,   // Read-only file system
    EMLINK           = 31,   // Too many links
    EPIPE            = 32,   // Broken pipe
    EDOM             = 33,   // Math argument out of domain of func
    ERANGE           = 34,   // Math result not representable
    EDEADLK          = 35,   // Resource deadlock would occur
    ENAMETOOLONG     = 36,   // File name too long
    ENOLCK           = 37,   // No record locks available
    ENOSYS           = 38,   // Function not implemented
    ENOTEMPTY        = 39,   // Directory not empty
    ELOOP            = 40,   // Too many symbolic links encountered
    ENOMSG           = 42,   // No message of desired type
    EIDRM            = 43,   // Identifier removed
    ENOSTR           = 60,   // Device not a stream
    ENODATA          = 61,   // No data available
    ETIME            = 62,   // Timer expired
    ENOSR            = 63,   // Out of streams resources
    ENOLINK          = 67,   // Link has been severed
    EPROTO           = 71,   // Protocol error
    EMULTIHOP        = 72,   // Multihop attempted
    EBADMSG          = 74,   // Not a data message
    EOVERFLOW        = 75,   // Value too large for defined data type
    EILSEQ           = 84,   // Illegal byte sequence
    ENOTSOCK         = 88,   // Socket operation on non-socket
    EDESTADDRREQ     = 89,   // Destination address required
    EMSGSIZE         = 90,   // Message too long
    EPROTOTYPE       = 91,   // Protocol wrong type for socket
    ENOPROTOOPT      = 92,   // Protocol not available
    EPROTONOSUPPORT  = 93,   // Protocol not supported
    EOPNOTSUPP       = 95,   // Operation not supported on transport endpoint
    EAFNOSUPPORT     = 97,   // Address family not supported by protocol
    EADDRINUSE       = 98,   // Address already in use
    EADDRNOTAVAIL    = 99,   // Cannot assign requested address
    ENETDOWN         = 100,  // Network is down
    ENETUNREACH      = 101,  // Network is unreachable
    ENETRESET        = 102,  // Network dropped connection because of reset
    ECONNABORTED     = 103,  // Software caused connection abort
    ECONNRESET       = 104,  // Connection reset by peer
    ENOBUFS          = 105,  // No buffer space available
    EISCONN          = 106,  // Transport endpoint is already connected
    ENOTCONN         = 107,  // Transport endpoint is not connected
    ETIMEDOUT        = 110,  // Connection timed out
    ECONNREFUSED     = 111,  // Connection refused
    EHOSTUNREACH     = 113,  // No route to host
    EALREADY         = 114,  // Operation already in progress
    EINPROGRESS      = 115,  // Operation now in progress
    ESTALE           = 116,  // Stale NFS file handle
    EDQUOT           = 122,  // Quota exceeded
    ECANCELED        = 125,  // Operation Canceled
    EOWNERDEAD       = 130,  // Owner died
    ENOTRECOVERABLE  = 131,  // State not recoverable
};

#endif
