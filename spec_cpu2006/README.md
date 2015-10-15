# Tools for GCC benchmarking

## Contents of this directory

This directory contains several scripts which are aimed at measuring compile times:
- `config.py.example` -- configuration parameters example (see the [Configuration] section)
- `build_spec.py` -- performs SPEC sources proprocessing. Generates shell script for measurements.
- `convert_result.py` -- aggregates and converts benchmark results
- `extract_lists.py` -- this script was used for generating `sources.yml` file (included for reference)

## Using the scripts

### 1. Installing prerequisites

In order to use the scripts you will need:
- A computer with GNU/Linux OS and an account with `sudo` privilege (see the [Benchmarking](.#4-benchmarking) section)

The following prerequisites must be installed:

- [SPEC CPU2006](https://www.spec.org/cpu2006/) benchmarks. You will need a license from the [Standard Performance Evaluation Corporation](https://www.spec.org/) to use them.
- Python 2.7.x (**TODO:** compatibility with Python 3.4.x)
- The following python packages (available via [pypi](https://pypi.python.org/pypi) package collection, i.e. `pip` or `easy_install`):
    - `sh` -- a wrapper for subprocess module
    - `pyYAML` -- YAML format reader/writer
- `perf` -- used for accurate run time measurement, part of `linux-tools` package
- [taskset](http://linux.die.net/man/1/taskset) -- used for binding threads to CPU cores (**FIXME:** use `numactl`), part of `util-linux` package
- [chrt](http://linux.die.net/man/1/chrt) -- used for setting static priority of a process, part of `util-linux` package
- GCC -- an **installed** copy is required for preprocessing the SPEC source code. 

Optional components:

- [TCMalloc](http://goog-perftools.sourceforge.net/doc/tcmalloc.html) -- alternative memory allocator (developed by Google)
- [jemalloc](http://www.canonware.com/jemalloc) -- alternative memory allocator (originally created by Facebook)
- Clang -- alternative compiler which can be used for reference purposes

#### Installation on Debian/Ubuntu

**TODO:** This has been checked for Debian 8. Need to verify for Ubuntu and adapt for Fedora.

Instructions:

1. Install the SPEC CPU2006 benchmark (according to the [guide](https://www.spec.org/cpu2006/Docs/install-guide-unix.html))
2. Install the required packages:

    `sudo apt-get install -y python python-pip linux-tools util-linux`

    `sudo pip2.7 install sh pyyaml`
3. Build and install GCC
4. _Optionally:_ install memory allocation libraries:
    `sudo apt-get install -y libtcmalloc-minimal4 libjemalloc1`
5. _Optionally:_ build and install LLVM/Clang
    
### 2. Configuration

Copy `spec_cpu2006/config.py.example` to `spec_cpu2006/config.py` and adjust the paths in this file to match your environment. These paths are:

- Directory containing SPEC CPU2006 benchmarks
- Directory containing an **installed** copy of GCC
- Temporary directory
- _Optionally: Directory containing installed Clang_

The comments in `config.py.example` should be self-explanatory.

### 3. Running the script

Run `./spec_cpu2006/build_spec.py -h` to get detailed help on available options.

#### Preprocessing 

Benchmarks work with preprocessed sources. You can preprocess the SPEC CPU2006 sources by running the following command from the repository root dir:
    
    ./spec_cpu2006/build_spec.py --preprocess
    
The preprocessed sources will be saved to the `preproc` subdirectory of the temporary directory specified in `config.py`

#### Generating benchmarking scripts

Benchmarking is performed by shell scripts: this allows you to look "under the hood" and see what exactly is measured. Example invocation:

    ./spec_cpu2006/build_spec.py --repeat 5

Will generate a set of scripts in the `timed_build` subdirectory of the temporary directory specified in `config.py`

### 4. Benchmarking

Run the benchmarking script as:

    sudo ./timed_build/build.sh ~/bench_data/log.txt
    
From you temporary directory. `sudo` is required for setting the FIFO scheduling policy, this allows to reduce noise in measured results.

### 5. Processing the results

Use the `spec_cpu2006/convert_result.py` script to postprocess the result:

    ./spec_cpu2006/convert_result.py ~/bench_data/log.txt ~/bench_data/result.csv
