#!/bin/bash

# This script is a functional 'smoke' test for
# spec_cpu2006/build_spec.py

# For now it just checks that no errors occur when running with some
# common options (output is NOT checked)

SCRIPT=$(readlink -e "$(dirname "$0")/../spec_cpu2006/build_spec.py")
EXIT_CODE=0

if [[ ! -e ${SCRIPT} ]]; then
    echo "Fatal error: script '${SCRIPT}' not found!" >&2
    exit 1
fi

function check
{
    echo -n "Running: $@..."
    if ! $SCRIPT "$@" >/dev/null; then
        echo ' FAILED!'
        EXIT_CODE=1
        return 1
    fi

    echo ' passed'
    return 0
}

if check --gcc --preprocess; then
    check
    check --gcc
    check --shell
    check --cxx98
    check -r 3
    check --with-gcc "${HOME}/gcc/build/gcc"

    check --alloc=ptmalloc
    check --alloc=tcmalloc
    check --alloc=jemalloc

    check -v
    check --mem-report
    check -O 'O1 finline-functions fdump-tree-optimized --alloc tcmalloc'
fi

if check --clang --preprocess; then
    check --clang
    check --clang --asm
    check --clang -v
    check --clang --cxx98
    check --clang -O 'O2 g'
    check --clang --alloc=tcmalloc
fi

if [[ ${EXIT_CODE} ]]; then
    echo 'All tests passed'
else
    echo 'Some tests FAILED'
fi

exit ${EXIT_CODE}
