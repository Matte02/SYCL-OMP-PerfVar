#!/bin/bash

ITER="100"
PATH_TO_CONFIG="/home/snazk/PerfVar/Repo/New/SYCL-OMP-PerfVar/noiseinjector/noise_config.json"
BENCHMARK="0"

for i in {0..2}
do
    for k in {7..8}
    do
        bash ./Benchmark.sh -i="$ITER" -t=1 -mt="$k" -m="$i" -b=0 -na="$PATH_TO_CONFIG"
    done
done
