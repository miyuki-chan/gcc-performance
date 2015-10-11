#!/usr/bin/env python2.7

# This script compiles SPEC CPU2006 benchmark using GCC, or generates
# shell script for compiling.
# It is intended for compilation time measurements. It can also
# calculate checksums of generated assembly files (to verify that some
# changes to GCC code do not affect codegen)

from __future__ import print_function

# System modules
import os, os.path, stat
from os.path import isdir
import multiprocessing, logging
import shutil
import sys
import argparse

# Local modules
import spec_flags
import config

# List of benchmarks which should be skipped, e.g.:
# SKIP = ['400.perlbench']
SKIP        = []

# Function aliases
pexists = os.path.exists
pjoin   = os.path.join

# Constants
SELF_DIR        = os.path.dirname(__file__)
SPEC_PATH       = pjoin(config.SPEC_PATH, 'benchspec', 'CPU2006')
ROOT_PATH       = config.WORK_PATH
SOURCES_YML     = pjoin(SELF_DIR, 'sources.yml')
DEFAULT_ALLOC   = 'ptmalloc'

# No-quite-constant. Set once before actual build
ALLOCATOR       = None

def error(msg):
    '''Output error message to stderr and exit with non-zero exit code'''
    sys.stderr.write('Error: {}\n'.format(msg))
    sys.exit(1)

# Import required modules. Error out, if failed
try:
    import sh
except:
    error('required package \'sh\' not found')

try:
    import yaml
except:
    error('required package \'pyYAML\' not found')

# Add md5sum program
try:
    from sh import md5sum
except:
    error('md5sum not found')


def perform_sanity_checks(args):
    '''Check that all required binaries and paths exist'''
    if not isdir(SPEC_PATH):
        error('directory \'{}\' does not exist!'
              ' Please set SPEC_PATH in config.py'.format(SPEC_PATH))
    if not isdir(ROOT_PATH):
        error('directory \'{}\' does not exist!'
              ' Please set WORK_PATH in config.py'.format(ROOT_PATH))

    if args.clang:
        if not isdir(config.CLANG_ROOT_PATH):
            error('directory \'{}\' does not exist!'
                  ' Please set CLANG_ROOT_PATH in config.py'
                  ' to use Clang'.format(CLANG_ROOT_PATH))
        global CLANG_PATH
        CLANG_PATH  = pjoin(config.CLANG_ROOT_PATH, 'bin')
        if not pexists(CLANG_PATH):
            error('file \'{}\' does not exist. Please set'
                  ' CLANG_ROOT_PATH correctly in config.py'.format(CLANG_PATH))
    else:
        if not pexists(pjoin(GCC_PATH, 'cc1')):
            error('cc1 binary does not exist in {}. Please'
                ' build the C compiler'.format(GCC_PATH))
        if not pexists(pjoin(GCC_PATH, 'cc1plus')):
            error('cc1plus binary does not exist in {}. Please'
                ' build the C++ compiler'.format(GCC_PATH))

def find_allocator(args):
    '''Find memory allocator library: search default paths and the
       path specified in ALLOCATORS dictionary in config.'''

    if config.ALLOCATORS[args.alloc]:
        path = config.ALLOCATORS[args.alloc]
        if not pexists(path):
            error('file \'{}\' not found. Please set'
                    ' ALLOCATORS correctly in config.py'.format(path))
        return path

    paths = {'tcmalloc': ['/usr/lib64/libtcmalloc_minimal.so',            # CentOS, Fedora
                        '/usr/lib/libtcmalloc_minimal.so.4'],             # Debian, Ubuntu

            'jemalloc': ['/usr/lib64/libjemalloc.so.1',                   # CentOS, Fedora
                        '/usr/lib/x86_64-linux-gnu/libjemalloc.so.1']}    # Debian, Ubuntu
    for path in paths[args.alloc]:
        if pexists(path):
            return path

    error('{} not found. Please set'
          ' ALLOCATORS manually in config.py'.format(args.alloc))

def find_gcc(args):
    '''Find the directory, which contains the compilers proper'''
    if args.with_gcc is not None:
        path = args.with_gcc
        if not pexists(path):
            error('{} not found'.format(path))
        return path

    if config.GCC_ROOT_PATH is None:
        error('GCC_ROOT_PATH not set in config.py')
    if not isdir(config.GCC_ROOT_PATH):
        error('directory \'{}\' does not exist.'
                ' Please set GCC_ROOT_PATH correctly in config.py'.format(config.GCC_ROOT_PATH))
    libexec_path = os.path.join(config.GCC_ROOT_PATH, 'libexec', 'gcc')
    if not isdir(libexec_path):
        error('directory \'{}\' does not exist.'
                ' Please set GCC_ROOT_PATH correctly in config.py'.format(libexec_path))
    arch_dir = os.listdir(libexec_path)[0]
    ver_dir = os.listdir(pjoin(libexec_path, arch_dir))[0]
    return pjoin(libexec_path, arch_dir, ver_dir)


def load_spec_lists():
    '''Load lists of SPEC sources'''
    with open(pjoin(SELF_DIR, 'sources.yml'), 'r') as f:
        return yaml.load(f)

INVOKE_PREFIX = 'taskset 0x00000001 chrt --fifo 99 '

LANG_C          = 'C'
LANG_CXX        = 'C++'
LANG_F          = 'Fortran'
LANG_FC         = 'C, Fortran'

COMPILER_FNAME  = {LANG_C:      'cc1',
                   LANG_CXX:    'cc1plus'}
# TODO: support Fortran
#                  LANG_F:      'f951'}

CLANG_FNAME     = {LANG_C:      'clang',
                   LANG_CXX:    'clang++'}

LANG_BY_PREPROC = {'.i':        LANG_C,
                   '.ii':       LANG_CXX}

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
    '''Worker function for child processed in multiprocess run'''
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
        sys.stdout.write('.')
        sys.stdout.flush()
        return res.split()[0].strip()
    except:
        return False


def compile_with_checksums(args):
    # FIXME: 1. Correctly handle options which gen_shell_scripts can handle
    #        2. Output checksums in some format usable by 'diff'
    '''Compile SPEC and calculate checksum of each compilation unit'''
    root_dir = pjoin(ROOT_PATH, 'preproc')
    BASE_OPTIONS = ['-O', '-w', '-quiet', '-o', '-', '-fpreprocessed']
    for bench in sorted(os.listdir(root_dir)):
        sys.stdout.write('Compiling {}: '.format(bench))
        options = BASE_OPTIONS[:] + spec_flags.CRUTCHES.get(bench, [])
        pool = multiprocessing.Pool() # Default number of workers is equal to num. of CPUs
        queue = []
        bench_dir = pjoin(root_dir, bench)
        for (ind, fname) in enumerate(sorted(os.listdir(bench_dir))):
            full_path = pjoin(bench_dir, fname)
            cmd = (full_path, options + ['-frandom-seed=' + str(ind)])
            queue.append(cmd)
        try:
            res = pool.map_async(compile_worker_func, queue, 1)
            pool.close()
            pool.join()
        except:
            error('Failed to compile '+bench)
        checksums = res.get()
        if any(v == False for v in checksums):
            error('Failed to compile \'{}\' (unknown error in child process)'.format(bench))
        sys.stdout.write('\n')
        print(checksums)


def preprocess_sources(args):
    data = load_spec_lists()
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

        defines = ['-D' + x for x in spec_flags.DEFS + spec_flags.OTHER_DEFS.get(name, [])]
        includes = ['-I' + x for x in spec_flags.INCLUDES.get(name, [])]
        options = defines + includes + spec_flags.CRUTCHES.get(name, [])
        if not args.clang:
            options.append('-quiet')
        if props['lang'] == LANG_CXX and args.cxx98:
            options.append('-std=c++98')

        for fname in props['sources']:
            full_path = pjoin(path, fname)
            base, _ = os.path.splitext(fname)
            preproc_name = base.replace('/', '_') + preproc_ext
            preproc_full = pjoin(preproc_dir, preproc_name)
            # TODO: spawn multiple processes to preprocess faster
            compiler('-E', '-o', preproc_full, full_path, *options)

def wrap_bind_aff_sched(args, cmd):
    return INVOKE_PREFIX + cmd

def wrap_perf(args, cmd, log_path):
    rep = '-r '+str(args.repeat) if args.repeat > 1 else ''
    return 'perf stat -d -x, {} -o {} --append {}'.format(rep, log_path, cmd)

def gen_shell_scripts(args):
    if args.clang:
        compiler_path_var = {LANG_C:    '$CC',
                             LANG_CXX:  '$CXX'}
    else:
        compiler_path_var = {LANG_C:    '$CC1',
                             LANG_CXX:  '$CC1PLUS'}

    compiler_flags_var    = {LANG_C:    '$CFLAGS',
                             LANG_CXX:  '$CXXFLAGS'}

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
    if args.clang:
        top_script.write('export CC=\'{0}/clang\'\nexport CXX=\'{0}/clang++\'\n'.format(CLANG_PATH))
    else:
        top_script.write('export CC1=\'{0}/cc1\'\nexport CC1PLUS=\'{0}/cc1plus\'\n'.format(GCC_PATH))
    opt_flags = ' '.join(['-' + opt for opt in args.optimization.split()])
    cxx_flags = ' -std=c++98' if args.cxx98 else ''
    top_script.write('export CFLAGS=\'{0}\'\n'
                     'export CXXFLAGS=\'{0}{1}\'\n'.format(opt_flags, cxx_flags))

    if args.alloc != DEFAULT_ALLOC:
        top_script.write('export LD_PRELOAD=\'{}\'\n'.format(ALLOCATOR))

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
        if args.clang:
            options.append('-S' if args.asm else '-c')
        else:
            options += ['-quiet', '-fpreprocessed']
            if args.mem_report:
                options.append('-fmem-report')
                args.verbose = True
        options += spec_flags.CRUTCHES.get(bench, [])
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
            if not args.clang:
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
    parser = argparse.ArgumentParser(description=
'''This script compiles or preprocesses SPEC CPU2006 benchmark sources
or generates a shell script for compiling them. It is intended for build
time measurement. It can also calculate checksums of generated
assembly files (to verify that some changes to the GCC code do not
affect codegen)''')

    action_grp = parser.add_mutually_exclusive_group()
    action_grp.add_argument('--preprocess', action='store_const', const=preprocess_sources,
                        dest='action', help='preprocess SPEC CPU2006 sources')
# FIXME: see comments in compile_with_checksums
#    action_grp.add_argument('--checksums', action='store_const', const=compile_with_checksums,
#                        dest='action', help='compile proceprocessed sources and calculate '
#                        'checksum of assembly')
    action_grp.add_argument('--shell', action='store_const', const=gen_shell_scripts,
                        dest='action', help='generate shell script for timed compilation (default)')
    parser.add_argument('--alloc', choices=[DEFAULT_ALLOC, 'tcmalloc', 'jemalloc'],
                        default='ptmalloc', help='alloctor to use (default: %(default)s)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='output timing information for each translation unit')
    parser.add_argument('--mem-report', action='store_true',
                        help='output memory report (implies verbose)')
    compiler_grp = parser.add_mutually_exclusive_group()
    compiler_grp.add_argument('--clang', action='store_true', help='benchmark Clang/Clang++')
    compiler_grp.add_argument('--gcc', action='store_true', help='benchmark GCC (default)')
    compiler_grp.add_argument('--with-gcc', metavar='GCC_DIR',
                        help='use GCC binaries (cc1, cc1plus) from specified directory')
    parser.add_argument('--asm', '--assembly', action='store_true',
                        help='when benchmarking Clang, produce assembly instead of object code')
    parser.add_argument('--cxx98', action='store_true', help='compile C++ code as C++98')
    parser.add_argument('-r', '--repeat', type=int, default=1,
                        help='number of times to compile each unit')
    parser.add_argument('-O', '--optimization', default='O3',
                        help='optimization options (default: %(default)s)')
    parser.set_defaults(action=gen_shell_scripts, alloc='ptmalloc')
    args = parser.parse_args()
    if args.clang and args.mem_report:
        parser.error('--mem-report is supported only with GCC')
    if args.asm and not args.clang:
        print('Warning: --asm (--assembly) is only meaningful for Clang'
              ' (GCC outputs assembly by default)')
    if args.action == preprocess_sources and args.with_gcc:
        parser.error('preprocessing can only be done using an installed version of GCC.'
                     ' Please set GCC_ROOT_PATH in config.py and use --gcc option')

    if not args.clang:
        global GCC_PATH
        GCC_PATH = find_gcc(args)

    if args.alloc != DEFAULT_ALLOC:
        global ALLOCATOR
        ALLOCATOR = find_allocator(args)

    perform_sanity_checks(args)

    compiler = (CLANG_PATH, CLANG_FNAME) if args.clang else \
               (GCC_PATH, COMPILER_FNAME)
    prepare_compilers_dict(*compiler)
    args.action(args)

if __name__ == '__main__':
    main()

