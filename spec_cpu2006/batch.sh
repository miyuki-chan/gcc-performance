#!/bin/bash -ex

BUILD_SPEC="${HOME}/scripts_gcc/spec/build_spec.py"
BUILD="${HOME}/ramdrive/timed_build/build.sh"
LOG_DIR="${HOME}/gcc/bench/build_spec_fdo"
NUM_ITER=5
TARGET='x86_64'
HOST='ivybridge'
HOST_TAGET="${HOST}/${TARGET}"

rm -rf "${LOG_DIR}"

if false; then
    "${BUILD_SPEC}" --clang --preprocess --cxx98
    for OPT in O0 Og O2 Ofast; do
        case ${OPT} in
            O0)
                OPT_ARG='O0 ggdb3'
                ;;
            Og)
                OPT_ARG='O1 fno-inline ggdb3'
                ;;
            O2)
                OPT_ARG='O2'
                ;;
            Ofast)
                OPT_ARG='O3 ffast-math mtune=haswell march=haswell'
                ;;
            *)
                exit 1
                ;;
        esac
        "${BUILD_SPEC}" --clang --cxx98 -O "${OPT_ARG}"
        DEST_DIR="${LOG_DIR}/${HOST}/clang/ptmalloc/${OPT}"
        mkdir -p "${DEST_DIR}"
        for (( i=1; i<=${NUM_ITER}; i++ )); do
            sudo "${BUILD}" "${DEST_DIR}/${i}.log"
        done
    done
fi

"${BUILD_SPEC}" --cxx98 --preprocess
#for ALLOC in ptmalloc tcmalloc jemalloc; do
for ALLOC in ptmalloc; do
    if [[ ${ALLOC} == 'ptmalloc' ]]; then
        ALLOC_ARG=''
        ALLOC=''
    else
        ALLOC_ARG="--${ALLOC}"
    fi
    for OPT in O0 Og O2 Ofast; do
        case ${OPT} in
            O0)
                OPT_ARG='O0 ggdb3'
                ;;
            Og)
                OPT_ARG='Og ggdb3'
                ;;
            O2)
                OPT_ARG='O2'
                ;;
            Ofast)
                OPT_ARG='Ofast march=haswell'
                ;;
            *)
                exit 1
                ;;
        esac
        "${BUILD_SPEC}" --cxx98 ${ALLOC_ARG} -O "${OPT_ARG}"
        DEST_DIR="${LOG_DIR}/${HOST}/gcc/${ALLOC}/${OPT}"
        mkdir -p "${DEST_DIR}"
        for (( i=1; i<=${NUM_ITER}; i++ )); do
            sudo "${BUILD}" "${DEST_DIR}/${i}.log"
        done
    done
done

