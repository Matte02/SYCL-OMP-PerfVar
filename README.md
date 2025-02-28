# SYCL-OMP-PerfVar

This repository contains benchmarks for analyzing reproducible performance variability in SYCL and OpenMP applications.

# Benchmarking and Noise Injection Usage Guide

The Benchmark.sh script is used to both execute workloads and use the noise injector. It requires sudo since it requires priviledges to set correct scheduling policies for the noise injector as well as alter system files to enable tracing and alter system behaviour. Log files, traces, noise injection configuration files, and graphs produced during execution are placed in the benchmarks/logs/THIS_RUN/

Warning: After running Benchmark.sh the system will be altered until reboot.

Several arguments can be passed to the scipt in order to configure its behaviour. These are listed below:

-i=XXXX This sets the amount of executions for each enabled framework and benchmark. Defaults to 1000.

-b=X This sets which singular benchmark to execute. Available benchmarks and corresponding X are: nbody (0), babelstream (1), miniFE (2).

-f=X This sets which singular framework to execute. Available frameworks and corresponding X are: OpenMP (0), SYCL (1).

-n=PATH_TO_NOISE_CONFIG This enables noise injection. PATH_TO_NOISE_CONFIG is the path to the noise_config.json file to utilize for noise injection. 

-t=X This disables and enables tracing by setting X to 0 respectively 1. By enabling tracing, the noise_config.json file is generated after the benchmark has executed all of its iterations and placed in benchmarks/logs/THIS_RUN/CURRENT_BENCHMARK/CURRENT_FRAMEWORK/ folder.

## Attribution

This project includes code and benchmarks from the following sources:

- **HPAS (High Performance Application Suite)**: The code in the `/HPAS/` directory is derived from the HPAS repository, which is maintained by Emre Ates. The original repository can be found at [https://github.com/peaclab/HPAS](https://github.com/peaclab/HPAS). The code is licensed under the BSD 3-Clause License. 
- **HeCBench**: The benchmarks in the `/benchmarks/` directory are derived from the HeCBench repository. The original repository can be found at [https://github.com/zjin-lcf/HeCBench](https://github.com/zjin-lcf/HeCBench). These benchmarks are also licensed under the BSD 3-Clause License.

Both HPAS and HeCBench have been modified and adapted for use in this project.


