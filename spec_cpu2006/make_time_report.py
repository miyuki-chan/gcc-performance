#!/usr/bin/env python2.7

import os, os.path
import sys
import re
import argparse

pjoin = os.path.join

ROOT_DIR    = os.path.expanduser('~/ramdrive/timed_build')
REF_REPORT  = pjoin(ROOT_DIR, 'rebase_8k_2a.txt')
TEST_REPORT = pjoin(ROOT_DIR, 'obstacks.txt')
TEST2_REPORT = None
#TEST2_REPORT = pjoin(ROOT_DIR, 'obstacks.txt')
#TEST2_REPORT = pjoin(ROOT_DIR, 'jemalloc.txt')

time_re = re.compile(r'(^|[^0-9.:])([0-9.:]+)([^0-9.:]|$)')

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

def parse_elapsed(ela):
    m, s = tuple(ela.split(':'))
    return float(s) + int(m) * 60


def parse_report(fname):
    result = {}
    with open(fname, 'r') as f:
        lines = f.readlines()
        benchmarks = chunks(lines, 3)
        for res in benchmarks:
            name = res[0].strip()
            time_matches = [m[1] for m in time_re.findall(res[1])]
            user = float(time_matches[0])
            system = float(time_matches[1])
            wall = parse_elapsed(time_matches[2])
            mem = int(time_matches[6])
            result[name] = (user, system, wall, mem)
    return result

def main(args):
    ref = parse_report(REF_REPORT)
    tests = [ parse_report(TEST_REPORT) ]
    if TEST2_REPORT is not None:
        tests.append(parse_report(TEST2_REPORT))
    col_names = ['user', 'sys', 'real']
    COL_SEP = '    '
    if not args.narrow:
        WIDTH = 6+6+10
        print 16 * ' ' + COL_SEP.join(['{:>22}'.format(name) for name in col_names])
    for bench in sorted(ref.keys()):
        ref_data = ref[bench]
        for test in tests:
            assert(bench in test)
            test_data = test[bench]
            cells = []
            for i, (x, y) in enumerate(zip(ref_data, test_data)[:3]):
                if x != 0 and y != 0:
                    diff = (y - x) / x
                    percent = '{:+.2%}'.format(diff)
                elif x == 0 and y != 0:
                    percent = ' 0.00%'
                else:
                    percent = '------'
                cell_text = '{:>6} {:>6} ({:>8})'.format(x, y, percent)
                if args.narrow:
                    cell_text += ' ' + col_names[i]
                cells.append(cell_text)
            if args.narrow:
                print '{:<16}{}'.format(bench, cells[0])
                for cell in cells[1:]:
                    print '{:<16}{}'.format('', cell)
            else:
                print '{:<16}{}'.format(bench, '    '.join(cells))

    for bench in sorted(ref.keys()):
        mem_ref = ref[bench][3]
        mem_test = test[bench][3]
        if TEST2_REPORT:
            mem_test2 = test2[bench][3]
            print '{0:<16}{1:>8}kB  {2:>8}kB  ({3:>+8}kB)  {4:>8}kB  ({5:>+8}kB)'.format(
                    bench, mem_ref, mem_test, mem_test - mem_ref, mem_test2, mem_test2 - mem_ref)
        else:
            print '{0:<16}{1:>8}kB  {2:>8}kB  ({3:>+8}kB)'.format(bench, mem_ref, mem_test, mem_test - mem_ref)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--narrow', action='store_true',
                        help='layout suitable for email')
    args = parser.parse_args()
    main(args)
