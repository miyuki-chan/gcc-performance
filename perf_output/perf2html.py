#!/usr/bin/env python

from __future__ import print_function

import sys
import os, os.path
import argparse

from perf.report import PerfReport

def error(message):
    sys.stderr.write(message + '\n')
    sys.exit(1)

def group(n, sep='\''):
    s = str(n)[::-1]
    groups = []
    i = 0
    while i < len(s):
        groups.append(s[i:i+3])
        i += 3
    return sep.join(groups)[::-1]


def generate(runs, output, args):
    have_stddev = runs[0].have_stddev
    have_multiple = len(runs) > 1
    # Write table tag
    if args.css_class is not None:
        output.write('<table class="{}">\n'.format(args.css_class))
    else:
        output.write('<table>\n')
    # Write header row
    output.write('<thead><tr>\n')
    output.write('  <th>Counter</th>\n')
    if have_multiple:
        for i in range(1, len(runs) + 1):
            output.write('  <th>Run {}</th>\n'.format(i))
    else:
        output.write('  <th>Value</th>\n')
        if have_stddev:
            output.write('  <th>Std. dev., %</th>\n')
    output.write('</tr></thead><tbody>\n')
    # Write actual data
    for key in runs[0].keys():
        output.write('<tr>\n')
        output.write('  <th>{}</th>\n'.format(key))
        for run in runs:
            if not key in run:
                output.write('  <td>-</td>\n')
                continue
            cell = run[key].value
            if isinstance(cell, int) and args.group:
                cell = group(cell)
            else:
                cell = str(cell)
            stddev = run[key].stddev
            # std. dev. in single cell with data
            if have_multiple and have_stddev:
                cell += ' ({:.2f} %)'.format(stddev)
            output.write('  <td>{}</td>\n'.format(cell))
            # std. dev. in a separate cell
            if not have_multiple and have_stddev:
                output.write('  <td>{:.2f}</td>\n'.format(stddev))
        output.write('</tr>\n')
    output.write('</tbody></table>\n')


def run(args):
    report = PerfReport(args.input, args.separator)
    if report.empty:
        error('No data!')
    generate(report, args.output, args)

def main():
    parser = argparse.ArgumentParser(description='Convert perf(1) report into HTML table')
    parser.add_argument('input', type=argparse.FileType('r'), help='input file')
    parser.add_argument('-o', '--output', type=argparse.FileType('w'),
                        help='output file (default: stdout)',
                        default=sys.stdout)
    parser.add_argument('-x', '--field-separator',
                        help='separator (should match perf invocation, default: \',\')',
                        default=',', dest='separator')
    parser.add_argument('--group', help='enable grouping (thousands separator)',
                        action='store_true')
    parser.add_argument('--class', help='CSS class for table',
                        dest='css_class')
    args = parser.parse_args()
    run(args)

if __name__ == '__main__':
    main()
