# *** CONFIGURATION ***

import os.path

# Root path of your SPEC installation.
# Should contain the 'benchspec' directory
SPEC_PATH           = os.path.expanduser('~/spec_cpu2006')

# Working directory for preprocessed sources and result output
# Should have ~1 GB free space. Ideally should reside on a ramdrive (i.e., tmpfs)
WORK_PATH           = os.path.expanduser('~/ramdrive')

# Path of you GCC installation
GCC_ROOT_PATH       = '/opt/gcc-6.0.0'

# You might also want to use the compiler proper from GCC build
# directory. In this case point GCC_BUILD_PATH to the directory
# where cc1 and cc1plus binaries reside. You should still set
# GCC_ROOT_PATH for preprocessing
# GCC_BUILD_PATH    = '/opt/gcc-6.0.0/libexec/gcc/x86_64-pc-linux-gnu/6.0.0'
GCC_BUILD_PATH      = None


# Path of Clang installation (only needed if you plan to benchmark Clang)
CLANG_ROOT_PATH     = '/opt/clang-3.7.0'
