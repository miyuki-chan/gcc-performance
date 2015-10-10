#!/bin/bash -e
SRC=${HOME}/spec_cpu2006/benchspec/CPU2006
DEST=${HOME}/ramdrive/CPU2006

mkdir -p "${DEST}"

cd "${SRC}"
for DIRNAME in $(ls -1 .)
do
    if [[ -d ${DIRNAME} ]]; then
        mkdir -p "${DEST}/${DIRNAME}"
        cp -r "${DIRNAME}/src" "${DEST}/${DIRNAME}"
    fi
done
