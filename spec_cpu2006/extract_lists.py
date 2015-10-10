#!/usr/bin/env python2.7

# This script collects lists of SPEC CPU2006 source files
# from build scripts.
# NYI for 447.dealII, because it's source is partially generated
# by the build system.

# List is output to stdout in yaml format. It is intended for
# use by buildspec.py

import os, os.path
import shutil
import yaml

SPEC_DIR = os.path.expanduser('~/spec_cpu2006/benchspec/CPU2006')

LANG_C      = 'C'
LANG_CXX    = 'C++'
LANG_F      = 'Fortran'
LANG_FC     = 'C, Fortran'

LANG_BY_EXT = {'.cc': LANG_CXX,
               '.cpp': LANG_CXX,
               '.C': LANG_CXX,
               '.f': LANG_F,
               '.f90': LANG_F,
               '.F': LANG_F,
               '.F90': LANG_F,
               '.c': LANG_C}

def main():
    data = {}
    for name in os.listdir(SPEC_DIR):
        if name in ['998.specrand', '999.specrand', '447.dealII']:
            continue
        full = os.path.join(top_dir, name)
        if os.path.isdir(full):
            obj_pm_path = os.path.join(full, 'Spec', 'object.pm')
            obj_pm = open(obj_pm_path, 'r')
            start = False
            src_list = []
            for line in obj_pm:
                if '@sources' in line:
                    start = True
                if start:
                    pos = line.rfind('(')
                    if pos >= 0:
                        line = line[pos+1:]
                    pos2 = line.find(')')
                    if pos2 >= 0:
                        line = line[:pos2]
                    src_list += line.strip().split()
                    if pos2 >= 0:
                        break
            obj_pm.close()
            langs = set()
            for fname in src_list:
                _, ext = os.path.splitext(fname)
                if ext not in LANG_BY_EXT:
                    print fname
                langs.add(LANG_BY_EXT[ext])
            if len(langs) == 1:
                lang = list(langs)[0]
            elif langs == set([LANG_C, LANG_F]):
                lang = LANG_FC
            else:
                print src_list
                print langs
                assert(False)
            data[name] = {}
            data[name]['sources'] = src_list
            data[name]['lang'] = lang
    print yaml.dump(data, default_flow_style=False)

if __name__ == '__main__':
    main()
