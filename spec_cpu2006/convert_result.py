#!/usr/bin/env python2.7

# This script converts results produced by scripts generated by build_spec.py

from __future__ import print_function

# System modules
import re
import os, os.path
import sys
import argparse

# Local modules
from perf_report import PerfReport, ReportError

def error(msg):
    '''Print error message to stderr and exit with non-zero status'''
    sys.stderr.write('Error: {}\n'.format(msg))
    sys.exit(1)

def to_num(s):
    try:
        return int(s)
    except ValueError:
        return float(s)

def process_file(src_name, dest, keys=[]):
    with open(src_name, 'r') as src:
        try:
            report = PerfReport(src, ',')
            if len(report) == 0:
                error('No data in ' + src_name)

            if len(keys) == 0:
                keys_set = set()
                # Use first 10 rows to guess which values have been measured
                for run in report[:10]:
                    keys_set |= set(run.keys())
                keys = list(sorted(keys_set))
                assert(len(keys) != 0)
                dest.write(','.join(['"{}"'.format(k) for k in ['name'] + keys]))

            for run in report:
                dest.write('"{}",'.format(run.name))
                line = ','.join([str(run[k].value) if k in run else '' for k in keys])
                dest.write(line + '\n')
        except ReportError as ex:
            error('Failed to parse \'{}\': {}'.format(src_name, ex))


def run(args):
    if os.path.isdir(args.input):
        files = [os.path.join(args.input, f) for f in os.listdir(args.input)]
        files = filter(os.path.isfile, files)
        if len(files) == 0:
            error('no files in the input directory')
        keys = []
        for full_path in files:
            process_file(full_path, args.output, keys)
    elif os.path.isfile(args.input):
        process_file(args.input, args.output)
    else:
        error('invalid input file')

def main():
    parser = argparse.ArgumentParser('aggregate and convert'
                ' GCC performance statistics produced by build_spec.py scripts')
    parser.add_argument('input',
                help='the directory containing input files or a single input file')
    parser.add_argument('output', type=argparse.FileType('w'),
                help='output file (in CSV format)')
    args = parser.parse_args()
    if not os.path.exists(args.input):
        parser.error('input file/directory does not exist')
    run(args)

if __name__ == '__main__':
    main()
