#pragma once

#include <inttypes.h>

// Ubuntu 24.04's gcc-arm-none-eabi 13.2 uses GCC's own <stdint.h>, so newlib 4.4.0's
// <inttypes.h> never sees __int64_t_defined and omits the PRI macros. Where a macro is
// missing, define it for this target. The assertions stop the build if the type
// sizes ever differ, and -Wformat checks every printf against the real types.

#ifndef PRIu32
#define PRIu32 "lu"
_Static_assert(__builtin_types_compatible_p(uint32_t, unsigned long),
               "PRIu32 fallback expects uint32_t to be unsigned long");
#endif

#ifndef PRIu64
#define PRIu64 "llu"
_Static_assert(__builtin_types_compatible_p(uint64_t, unsigned long long),
               "PRIu64 fallback expects uint64_t to be unsigned long long");
#endif

#ifndef PRId64
#define PRId64 "lld"
_Static_assert(__builtin_types_compatible_p(int64_t, long long),
               "PRId64 fallback expects int64_t to be long long");
#endif
