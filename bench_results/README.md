# Benchmark results

This directory contains some benchmark results.

## Applications under test

The following versions of GCC and Clang were tested:

| **Application** | **Description**                                                   |
|-----------------|-------------------------------------------------------------------|
| GCC             | gcc version 6.0.0 20150923 (experimental) (GCC), r228065          |
| Clang           | clang version 3.7.0 (tags/RELEASE_370/final)                      |

Revision r228065 was chosen because it was the head revision when I started collecting data for this benchmark set.

## Flag sets

Each benchmark was performed with 4 different sets of compilation flags, corresonding to some (I believe) typical use cases:

| **Name** | **Description**         | **Flags for GCC**       | **Flags for Clang**                             |
|----------|-------------------------|-------------------------|-------------------------------------------------|
| `O0`     | Debug build             | `-O0 -ggdb3`            | `-O0 -ggdb3`                                    |
| `Og`     | Performance debug build | `-Og -ggdb3`            | `-O1 -fno-inline -ggdb3`                        |
| `O2`     | Release build           | `-O2`                   | `-O2`                                           |
| `Ofast`  | Tuned release build     | `-Ofast -march=haswell` | `-O3 -ffast-math -march=haswell -mtune=haswell` |

_Note:_ this benchmark does not aim at comparing GCC and Clang. Obviously, `-O2` for GCC is not the same as `-O2` for Clang.
The purpose of benchmarking Clang is to find areas where optimization is needed most (i.e. where our competitor has
significant advantage).

## Hosts

Benchmarking was performed on two different hosts (subdirectories correspond to hosts). Both are x86\_64-linux (Debian 8).

| **Name**    | **Environment**        | **CPU**                                              | **RAM** |
|-------------|------------------------|------------------------------------------------------|---------|
| `ivybridge` | with running X-session | Intel(R) Core(TM) i7-3770K CPU @ 3.50GHz (Ivybridge) | 16 GB   |
| `haswell`   | "headless"             | Intel(R) Core(TM) i7-5820K CPU @ 3.30GHz (Haswell)   | 32 GB   |

Some benchmarks were done only on `ivybridge` host.

**FIXME:** add info about RAM timings.


## Benchmark sets

### Bootstrap compiler

This set containts 3 benchmarks which differ by compiler being used:

| **Name**   | **Description**                                          |
|------------|----------------------------------------------------------|
| `gcc_52`   | Compiled using GCC 5.2.0 (with disabled bootstrap)       |
| `boot`     | Bootstrapped with default options                        |
| `boot_fdo` | Profile-bootstraped with default options                 |

### Memory allocator

| **Name**   | **Description**                                                |
|------------|----------------------------------------------------------------|
| `ptmalloc` | Same as `gcc_52`                                               |
| `tcmalloc` | Same as `gcc_52` with preloaded `libtcmalloc_minimal.so.4.2.2` |
| `jemalloc` | Same as `gcc_52` with preloaded `libjemalloc.so.1`             |