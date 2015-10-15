# GCC benchmarking tools and results

This repository is intended for GCC developers. It contains the data on GCC performance (in terms of compile time) on a certain (fairly large) set of workloads in various conditions. It also contains the scripts which were used to collect the data.

## Sample use cases

The collected data may help you get the answers on such questions as:

1. Do we have some degenerate cases where the optimized build takes suspiciously long time to build (possible compile time hogs)?
2. How does the bootstrap compiler affect GCC performance (i.e. disabled bootstrap vs. bootstrap vs. profiled bootstrap)? Which benchmarks are affected most?
3. How does the memory allocator affect performance?
4. How does the host CPU u-arch affect performance?

**TODO: Add examples!** See [Examples](examples/README.md).

## Workloads

For now the C and C++ code from [SPEC CPU2006](https://www.spec.org/cpu2006/) benchmark is used as workload.

_Note: I also plan to add benchmarks for Firefox sources and other freely available popular code._

### Legal notice

This repository does not contain any part of the SPEC benchmark itself. It also does not contain any SPEC benchmark
results (only compile time is analyzed).

## Contents

### Performance data

The data can be used to analyze GCC performance and select workloads which best suite the area you work on.

See [Benchmark results](bench_results/README.md) for details on available data and their format.

### Scripts for performance measurement

The scripts can be used by several categories of developers:
* Those who work on improving performance of GCC can use these scripts to measure the effect of their improvements
* Those who make functional changes (e.g. create a new optimization pass, etc.) can use the scripts to measure the
impact of their changes on performance
* Those who make non-functional changes (refactoring) can use the scripts to verify that code generation is not
affected by their changes and also measure the impact on performance

See [Tools for GCC benchmarking](spec_cpu2006/README.md) for details.

## Planned improvements

1. Support other code bodies (Firefox, boost, hana, GCC bootstrap)
2. Support LTO
3. Fortran benchmarks
4. Code with openmp
5. Synthetic benchmarks which stress the C++ frontend
6. Aggregate and publish SUSE periodic tests
