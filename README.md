# GCC performance benchmarking tools and results

This repository is intended for GCC developers.

## Introduction
This repository contains some raw data on GCC performance measured on a certain big set of workloads
(source code) in different conditions. It also contains scripts which were used to collect the data.

The collected data may help you get the answers on such questions as:

1. Do we have some degenerate cases where the optimized build takes ~20x time of non-optimized one (and Clang
spends resonable time without negative implications on codegen)?
2. How does FDO affect GCC performance? Which source code constructs are compiled especially fast by
an FDO-optimized compiler. Does FDO regress performance in some cases?
3. How does memory allocator affect the performance (e.g., would it be better to use TCMalloc? or jemalloc? On which
workloads and compile options this is especially noticable)?

## Goals

### Performance data
The data can be used to analyze GCC performance and select workload which best suites as test for the area you
work on.

### Scripts for performance measurement
The scripts can be used by several categories of developers:
* Those who work on improving performance of GCC can use these scripts to measure the effect of their improvements
* Those who make functional changes (e.g. create a new optimization pass, etc.) can use the scripts to measure the
impact of their changes on performance
* Those who make non-functional changes (refactoring) can use the scripts to verify that code generation is not
affected by their changes and also measure the impact on performance

## Workload
For now the C and C++ code from [SPEC CPU2006](https://www.spec.org/cpu2006/) benchmark is used as workload.
You must have a license from [Standard Performance Evaluation Corporation](https://www.spec.org/) to use them.

_Note: I also plan to add benchmarks for Firefox sources and other freely available popular code._

### Disclaimer
This repository does not contain any part of the SPEC benchmark itself. It also does not contain any SPEC benchmark
results (only compile time is analyzed).

## Prerequisites

### Using the data
You may use any tools to analyze published performance data: it's in CSV format and should be importable by any
popular statisctics software, such as R. Nevertheless this repository contains some aggreggated results in
Python Jupyter format. In order to use them you will need:

1. Python 2.7.x (**FIXME:** compatibility with Python 3.4.x)
2. [Jupyter](https://jupyter.org) notebook (**FIXME**: check if IPython is enough)
3. [pandas](http://pandas.pydata.org) data analysis library, version 0.16+
4. [matplotlib](http://matplotlib.org), version 1.4+

### Measuring performance
In order to perform measurements yourself, you will need:

1. GNU/Linux OS and an account with `sudo` privilege (see later)
2. Python 2.7.x and the following packages (available via `pip`):
    1. `sh`
    2. `pyYAML`
3. Installed copy of [SPEC CPU2006](https://www.spec.org/cpu2006/) benchmark
4. `perf`
5. `taskset` (**FIXME**: add support for `numactl`)
6. `chrt`
7. The compiler you are planning to test (the compiler proper, i.e. `cc1` and `cc1plus` is enough,
but an installed compiler will, of course, also work)

## TODO

**Add a manual**

## Planned improvements

1. Support other code bodies (Firefox, boost, hana, GCC bootstrap)
2. Support LTO
3. Fortran benchmarks
4. Code with openmp
5. Synthetic benchmarks which stress the C++ frontend
6. Aggregate and publish SUSE periodic tests
