#!/usr/bin/env python2.7

# This script compiles SPEC CPU2006 benchmark using GCC, or generates
# shell script for compiling.
# It is intended for compilation time measurements. It can also
# calculate checksums of generated assembly files (to verify that some
# changes to GCC code do not affect codegen)

from __future__ import print_function
from spec_pkg import flags

import os, os.path, stat

import multiprocessing, logging
import shutil
import yaml
import sys
import sh
import argparse
from sh import md5sum

LANG_C      = 'C'
LANG_CXX    = 'C++'
LANG_F      = 'Fortran'
LANG_FC     = 'C, Fortran'

ROOT_PATH   = os.path.expanduser('~/ramdrive')
SPEC_PATH   = os.path.expanduser('~/spec_cpu2006/benchspec/CPU2006')

#GCC_PATH    = '/opt/gcc-6.0.0/libexec/gcc/x86_64-pc-linux-gnu/6.0.0'
GCC_PATH    = '/opt/gcc-6.0.0-fdo/libexec/gcc/x86_64-pc-linux-gnu/6.0.0'
CLANG_PATH  = '/opt/clang-3.7.0/bin'

INVOKE_PREFIX = 'taskset 0x00000001 chrt --fifo 99 '
HOST_OS     = 'Debian'

if HOST_OS == 'CentOS':
    TCMALLOC_PREFIX = 'export LD_PRELOAD=/usr/lib64/libtcmalloc_minimal.so'
    JEMALLOC_PREFIX = 'export LD_PRELOAD=/usr/lib64/libjemalloc.so.1'
else:
    TCMALLOC_PREFIX = 'export LD_PRELOAD=/usr/lib/libtcmalloc_minimal.so.4'
    JEMALLOC_PREFIX = 'export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.1'


SKIP        = [\
#   '400.perlbench', '401.bzip2',
#   '403.gcc', '429.mcf',
#   '433.milc', '444.namd',
#   '445.gobmk', '450.soplex',
#   '453.povray', '456.hmmer',
#   '458.sjeng', '462.libquantum',
#   '464.h264ref', '470.lbm',
#   '471.omnetpp', '473.astar',
#   '482.sphinx3', '483.xalancbmk',
]

COMPILER_FNAME  = { LANG_C:      'cc1',
                    LANG_CXX:    'cc1plus',
                    LANG_F:      'f951' }
CLANG_FNAME     = { LANG_C:      'clang',
                    LANG_CXX:    'clang++' }

LANG_BY_PREPROC = { '.i':   LANG_C,
                    '.ii':  LANG_CXX }

pjoin = os.path.join

compilers = {}

def prepare_compilers_dict(bin_dir, binaries):
    global compilers
    for (lang, fname) in binaries.items():
        path = pjoin(bin_dir, fname)
        if os.path.exists(path):
            compilers[lang] = sh.Command(path)
            print('{} compiler: \'{}\''.format(lang, path))
        else:
            print('\'{}\' not found!'.format(path))


def compile_worker_func(cmd):
    full_path, options = cmd
    fname = os.path.basename(full_path)
    _, ext = os.path.splitext(fname)
    if ext not in LANG_BY_PREPROC:
        return False
    lang = LANG_BY_PREPROC[ext]
    compiler = compilers[lang]
    options.append(full_path)
    try:
        res = md5sum(compiler(*options))
        return res.split()[0].strip()
    except:
        return False

def compile_with_checksums(args):
    pool = multiprocessing.Pool() # Default number of workers is equal to num. of CPUs
    root_dir = pjoin(ROOT_PATH, 'preproc')
    queue = []
    for bench in os.listdir(root_dir):
        options = ['-O', '-w' '-quiet', '-o', '-', '-fpreprocessed']
        options += flags.CRUTCHES.get(bench, [])
        bench_dir = pjoin(root_dir, bench)
        for (ind, fname) in enumerate(sorted(os.listdir(bench_dir))):
            full_path = pjoin(bench_dir, fname)
            cmd = (full_path, options + ['-frandom-seed=' + str(ind)])
            queue.append(cmd)
    res = pool.map_async(compile_worker_func, queue[:10], 1)
    checksums = res.get()
    pool.close()
    pool.join()


def preprocess_sources(args):
    self_dir = os.path.dirname(__file__)
    f = open(pjoin(self_dir, 'sources.yml'), 'r')
    data = yaml.load(f)
    f.close()

    for name in sorted(data.keys()):
        props = data[name]
        lang = props['lang']

        if props['lang'] in [LANG_F, LANG_FC]:
            continue

        compiler = compilers[lang]
        path = pjoin(SPEC_PATH, name, 'src')
        preproc_dir = pjoin(ROOT_PATH, 'preproc', name)
        if not os.path.exists(preproc_dir):
            os.makedirs(preproc_dir)
        os.chdir(path)
        preproc_ext = '.ii' if props['lang'] == LANG_CXX else '.i'

        print('Preprocessing: {}'.format(name))

        defines = ['-D' + x for x in flags.DEFS + flags.OTHER_DEFS.get(name, [])]
        includes = ['-I' + x for x in flags.INCLUDES.get(name, [])]
        options = defines + includes + flags.CRUTCHES.get(name, [])
        if not args.clang:
            options.append('-quiet')
        if props['lang'] == LANG_CXX and args.cxx98:
            options.append('-std=c++98')

        for fname in props['sources']:
            full_path = pjoin(path, fname)
            base, _ = os.path.splitext(fname)
            preproc_name = base.replace('/', '_') + preproc_ext
            preproc_full = pjoin(preproc_dir, preproc_name)
            compiler('-E', '-o', preproc_full, full_path, *options)

def wrap_bind_aff_sched(args, cmd):
    return INVOKE_PREFIX + cmd

def wrap_perf(args, cmd, log_path):
    rep = '-r '+str(args.repeat) if args.repeat > 1 else ''
    return 'perf stat -d -x, {} -o {} --append {}'.format(rep, log_path, cmd)

def gen_shell_scripts(args):
    is_clang = args.clang
    if is_clang:
        compiler_path_var = {LANG_C:    '$CC',
                             LANG_CXX:  '$CXX'}
    else:
        compiler_path_var = {LANG_C:    '$CC1',
                             LANG_CXX:  '$CC1PLUS'}
    compiler_flags_var = {LANG_C:   '$CFLAGS',
                          LANG_CXX: '$CXXFLAGS'}
    perm = stat.S_IRUSR + stat.S_IWUSR + stat.S_IXUSR + \
           stat.S_IRGRP +                stat.S_IXGRP + \
           stat.S_IROTH +                stat.S_IXOTH # 0755
    output_dir = pjoin(ROOT_PATH, 'timed_build')
    print('Generating scripts in \'{}\''.format(output_dir))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    preproc_dir = pjoin(ROOT_PATH, 'preproc')
    top_script = open(pjoin(output_dir, 'build.sh'), 'w')
    top_script.write('#!/bin/bash -e\n')
    if is_clang:
        top_script.write('export CC=\'{0}/clang\'\nexport CXX=\'{0}/clang++\'\n'.format(CLANG_PATH))
    else:
        top_script.write('export CC1=\'{0}/cc1\'\nexport CC1PLUS=\'{0}/cc1plus\'\n'.format(GCC_PATH))
    opt_flags = ' '.join(['-' + opt for opt in args.optimization.split()])
    cxx_flags = ' -std=c++98' if args.cxx98 else ''
    top_script.write('export CFLAGS=\'{0}\'\n'
                     'export CXXFLAGS=\'{0}{1}\'\n'.format(opt_flags, cxx_flags))
    if args.alloc:
        top_script.write(args.alloc + '\n')
    invoke_prefix = INVOKE_PREFIX
    log_path = '"$1"'
    top_script.write('rm -f {}\n'.format(log_path))
    prefix1 = 'time ' if args.verbose else ''
    for bench in sorted(os.listdir(preproc_dir)):
        dest_path = pjoin(output_dir, bench + '.sh')
        dest = open(dest_path, 'w')
        dest.write('#!/bin/bash -e\n')
        bench_dir = pjoin(preproc_dir, bench)
        options = ['-o', '/dev/null', '-w']
        if is_clang:
            options.append('-S')
        else:
            options += ['-quiet', '-fpreprocessed']
            if args.mem_report:
                options.append('-fmem-report')
                args.verbose = True
        options += flags.CRUTCHES.get(bench, [])
        options = ' '.join(options)
        fnames = os.listdir(bench_dir)
        MARK_STEP = 0.1
        next_mark = MARK_STEP
        for ind, fname in enumerate(sorted(fnames)):
            lang = LANG_BY_PREPROC[os.path.splitext(fname)[1]]
            path_var = compiler_path_var[lang]
            flags_var = compiler_flags_var[lang]
            tu_path = pjoin(bench_dir, fname)
            cmd_parts = [path_var, options]
            if not is_clang:
                cmd_parts.append('-frandom-seed=' + str(ind))
            cmd_parts += [flags_var, tu_path]
            cmd = ' '.join(cmd_parts)
            cmd = wrap_perf(args, cmd, log_path)
            cmd = wrap_bind_aff_sched(args, cmd)
            dest.write('echo \'# WORKLOAD: {}/{}\' >> {}\n'.format(bench, fname, log_path))
            dest.write(cmd + ' 2>&1\n')
            if args.verbose:
                dest.write('echo \'# {}\'\n'.format(fname))
            else:
                pos = float(ind) / len(fnames)
                if pos >= next_mark:
                    mark = '[ {:.1%} ].'.format(pos)
                    next_mark += MARK_STEP
                else:
                    mark = '.'
                dest.write('echo -n \'{}\'\n'.format(mark))
        dest.write('echo\n')
        dest.close()
        os.chmod(dest_path, perm)
        top_script.write('echo \'{0}\'\n'
                         'echo \'# {0}\' >> {2}\n'
                         '{1}/{0}.sh {2} 2>&1\n'.format(
                         bench, output_dir, log_path))
    top_script.close()
    os.chmod(pjoin(output_dir, 'build.sh'), perm)
    print('Done!')

def main():
    parser = argparse.ArgumentParser()
    action_grp = parser.add_mutually_exclusive_group()
    action_grp.add_argument('--preprocess', action='store_const', const=preprocess_sources,
                        dest='action', help='preprocess SPEC CPU2006 sources')
    action_grp.add_argument('--checksums', action='store_const', const=compile_with_checksums,
                        dest='action', help='compile proceprocessed sources and calculate '
                        'checksum of assembly')
    action_grp.add_argument('--shell', action='store_const', const=gen_shell_scripts,
                        dest='action', help='generate shell script for timed compilation (default)')
    alloc_grp = parser.add_mutually_exclusive_group()
    alloc_grp.add_argument('--jemalloc', action='store_const', dest='alloc', const=JEMALLOC_PREFIX,
                        help='preload JEMalloc memory allocator')
    alloc_grp.add_argument('--tcmalloc', action='store_const', dest='alloc', const=TCMALLOC_PREFIX,
                        help='preload TCMalloc memory allocator')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='output timing information for each translation unit')
    parser.add_argument('--mem-report', action='store_true',
                        help='output memory report (implies verbose)')
    parser.add_argument('--clang', action='store_true', help='benchmark Clang/Clang++')
    parser.add_argument('--cxx98', action='store_true', help='compile C++ code as C++98')
    parser.add_argument('-r', '--repeat', type=int, default=1,
                        help='number of times to compile each unit')
    parser.add_argument('-O', '--optimization', default='O3',
                        help='optimization options (default: %(default)s)')
    parser.set_defaults(action=gen_shell_scripts, alloc='')
    args = parser.parse_args()
    prepare_compilers_dict(CLANG_PATH if args.clang else GCC_PATH,
                           CLANG_FNAME if args.clang else COMPILER_FNAME)
    args.action(args)

if __name__ == '__main__':
    main()

