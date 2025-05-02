#!/bin/bash
ITER="200"

BASELINE_FOLDER=/home/snazk/PerfVar/Repo/New/SYCL-OMP-PerfVar/benchmarks/logs/ThreadPin-benchmark-no-miniFE-sycl/babelstream-omp
python3 ./traces_to_noise_config.py $BASELINE_FOLDER -o hybrid-config.json -w main

PATH_TO_CONFIG=/home/snazk/PerfVar/Repo/New/SYCL-OMP-PerfVar/scripts/hybrid-config.json
FOLDER_NAME=CompareBabelstream-Hybrid-TP-28
BENCHMARK="1"

bash ./Benchmark.sh -f=0 -i=200 -t=0 -mt=8 -m=1 -b="$BENCHMARK" -folder_name="$FOLDER_NAME/TrialNice19rep" -na=$PATH_TO_CONFIG





