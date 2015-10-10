# *** CONFIGURATION ***

import os.path

# Root path of your SPEC installation.
# Should contain the 'benchspec' directory
SPEC_PATH           = os.path.expanduser('~/spec_cpu2006')

# Working directory for preprocessed sources and result output
# Should have ~1 GB free space. Ideally should reside on a ramdrive (i.e., tmpfs)
WORK_PATH           = os.path.expanduser('~/ramdrive')

# Path of your GCC installation
# It will be used for preprocessing the source code of SPEC
# If you don't specify a different compiler when performing
# the benchmark, this compiler will also be used for benchmarking
GCC_ROOT_PATH       = '/opt/gcc-6.0.0'

# Path of Clang installation (only needed if you plan to benchmark Clang)
CLANG_ROOT_PATH     = '/opt/clang-3.7.0'

# You can use non-standard memory allocator (tcmalloc or jemalloc) for
# benchmark. If you use the corresponding option, it will be searched
# in the standard locations. You can explicitly specify the paths here
ALLOCATORS = {
    # Path of libtcmalloc_minimal.so.
    # Set it manually, if needed but not found automatically
    'tcmalloc': None,

    # Path of libjemalloc.so.1. Likewise.
    'jemalloc': None
}

