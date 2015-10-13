# Tools for benchmarking GCC performance on SPEC CPU2006 sources

## Contents of this directory

This directory contains several scripts which are aimed at measuring compile times:
- `config.py.example` -- configuration parameters example (see [Configuration] section)
- `build_spec.py` -- performs SPEC sources proprocessing. Generates shell script for measurements. Run
    ```build_spec.py -h```
to get additional information
- `convert_result.py` -- aggregates and converts benchmark results
- `extract_lists.py` -- this script was used for generating `sources.yml` file (included for reference)

## Using the scripts

### 1. Installing prerequisites

In order to use the scripts, the following prerequisites must be installed:

- Python 2.7.x
- The following python packages (available via [pypi](https://pypi.python.org/pypi) package collection, i.e. `pip` or `easy_install`):
    - `sh` -- wrapper for subprocess module
    - `pyYAML` -- YAML format reader/writer
- `perf` (part of `linux-tools` package) -- used for accurate run time measurement
- [taskset](http://linux.die.net/man/1/taskset) -- used for binding threads to CPU cores (**FIXME:** use `numactl`)
- [chrt](http://linux.die.net/man/1/chrt) -- used for setting static priority of a process
- GCC -- an **installed** copy is required for preprocessing

Optional components:

- [TCMalloc](http://goog-perftools.sourceforge.net/doc/tcmalloc.html) -- alternative memory allocator (developed by Google)
- [jemalloc](http://www.canonware.com/jemalloc) -- alternative memory allocator (originally created by Facebook)
- Clang -- alternative compiler which can be used for reference purposes
    
### 2. Configuration

Copy `config.py.example` to `config.py` and adjust paths in this file to match your environment. These paths are:

- Directory containing installed SPEC CPU2006 benchmark
- Directory containing **installed** GCC
- Temporary directory
- _Optionally: Directory containing installed Clang_

The comments in `config.py.example` should be self-explanatory.

### 3. Preprocessing

Preprocess the SPEC CPU2006 source by running
    
    build_spec.py --preprocess
    
The preprocessed sources will be saved to the temporary directory specified in `config.py`

### 4. Generating benchmark scripts

### 5. Benchmarking

### 6. Processing results