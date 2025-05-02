#!/bin/bash
#ITER="1000"
#for f in {0..1}
#do
#    i=0
#    k=6
#    #bash ./Benchmark.sh -f=$f -i="$ITER" -t=1 -mt="$k" -m="$i" -b=0 -folder_name="BaselinesNbody/$i-$k-$f"
#    #wait 10
#
#    bash ./Benchmark.sh -f=$f -i="$ITER" -t=1 -mt="$k" -m="$i" -b=1 -folder_name="BaselinesBabelstream/$i-$k-$f"
#    wait 10
#
#    bash ./Benchmark.sh -f=$f -i="$ITER" -t=1 -mt="$k" -m="$i" -b=2 -folder_name="BaselinesMiniFE/$i-$k-$f"
#    wait 10
#done
#
#bash ./Benchmark.sh -f=1 -i="$ITER" -t=1 -mt="$k" -m="$i" -b=0 -folder_name="BaselinesNbody/$i-$k-1"
#wait 10

ITER="200"

BASELINE_FOLDER=/home/snazk/PerfVar/Repo/New/SYCL-OMP-PerfVar/benchmarks/logs/BaselinesMiniFE/TPHKx2/miniFE-omp
python3 ./traces_to_noise_config.py $BASELINE_FOLDER -o hybrid-config.json -w miniFE.x

PATH_TO_CONFIG=/home/snazk/PerfVar/Repo/New/SYCL-OMP-PerfVar/scripts/hybrid-config.json
FOLDER_NAME=CompareMiniFE-Comb-TPHKx2-21
BENCHMARK=2

for f in {0..1}
do
    bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt=6 -m=0 -b="$BENCHMARK" -folder_name="$FOLDER_NAME/0-6-$f" -na=$PATH_TO_CONFIG
    wait 10

    for i in {0..2}
    do
        k=8
        bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt="$k" -m="$i" -b="$BENCHMARK" -folder_name="$FOLDER_NAME/$i-$k-$f" -na=$PATH_TO_CONFIG
    done
    
    bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt=7 -m=0 -b="$BENCHMARK" -folder_name="$FOLDER_NAME/0-7-$f" -na=$PATH_TO_CONFIG
    bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt=7 -m=2 -b="$BENCHMARK" -folder_name="$FOLDER_NAME/2-7-$f" -na=$PATH_TO_CONFIG
done 


BASELINE_FOLDER=/home/snazk/PerfVar/Repo/New/SYCL-OMP-PerfVar/benchmarks/logs/No-Threadpin-omp-11-03-2025-00:43:43/nbody-omp
python3 ./traces_to_noise_config.py $BASELINE_FOLDER -o hybrid-config.json -w main

PATH_TO_CONFIG=/home/snazk/PerfVar/Repo/New/SYCL-OMP-PerfVar/scripts/hybrid-config.json
FOLDER_NAME=CompareNbody-Comb-Roam-0625
BENCHMARK="0"

for f in {0..1}
do
    bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt=6 -m=0 -b="$BENCHMARK" -folder_name="$FOLDER_NAME/0-6-$f" -na=$PATH_TO_CONFIG
    wait 10

    for i in {0..2}
    do
        k=8
        bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt="$k" -m="$i" -b="$BENCHMARK" -folder_name="$FOLDER_NAME/$i-$k-$f" -na=$PATH_TO_CONFIG
    done
    bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt=7 -m=0 -b="$BENCHMARK" -folder_name="$FOLDER_NAME/0-7-$f" -na=$PATH_TO_CONFIG
    bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt=7 -m=2 -b="$BENCHMARK" -folder_name="$FOLDER_NAME/2-7-$f" -na=$PATH_TO_CONFIG
done 


BASELINE_FOLDER=/home/snazk/PerfVar/Repo/New/SYCL-OMP-PerfVar/benchmarks/logs/ThreadPin-benchmark-no-miniFE-sycl/babelstream-omp
python3 ./traces_to_noise_config.py $BASELINE_FOLDER -o hybrid-config.json -w main

PATH_TO_CONFIG=/home/snazk/PerfVar/Repo/New/SYCL-OMP-PerfVar/scripts/hybrid-config.json
FOLDER_NAME=CompareBabelstream-Comb-TP-28
BENCHMARK="1"
for f in {0..1}
do
    bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt=6 -m=0 -b="$BENCHMARK" -folder_name="$FOLDER_NAME/0-6-$f" -na=$PATH_TO_CONFIG
    wait 10
    for i in {0..2}
    do
        k=8
        bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt="$k" -m="$i" -b="$BENCHMARK" -folder_name="$FOLDER_NAME/$i-$k-$f" -na=$PATH_TO_CONFIG
    done

    bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt=7 -m=0 -b="$BENCHMARK" -folder_name="$FOLDER_NAME/0-7-$f" -na=$PATH_TO_CONFIG
    bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt=7 -m=2 -b="$BENCHMARK" -folder_name="$FOLDER_NAME/2-7-$f" -na=$PATH_TO_CONFIG
done 









BASELINE_FOLDER=/home/snazk/PerfVar/Repo/New/SYCL-OMP-PerfVar/benchmarks/logs/BaselinesMiniFE/Roam/miniFE-omp
python3 ./traces_to_noise_config.py $BASELINE_FOLDER -o hybrid-config.json -w miniFE.x

PATH_TO_CONFIG=/home/snazk/PerfVar/Repo/New/SYCL-OMP-PerfVar/scripts/hybrid-config.json
FOLDER_NAME=CompareMiniFE-Comb-Roam-134
BENCHMARK="2"

for f in {0..1}
do
    bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt=6 -m=0 -b="$BENCHMARK" -folder_name="$FOLDER_NAME/0-6-$f" -na=$PATH_TO_CONFIG
    wait 10

    for i in {0..2}
    do
        k=8
        bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt="$k" -m="$i" -b="$BENCHMARK" -folder_name="$FOLDER_NAME/$i-$k-$f" -na=$PATH_TO_CONFIG
        wait 10
    done

    bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt=7 -m=0 -b="$BENCHMARK" -folder_name="$FOLDER_NAME/0-7-$f" -na=$PATH_TO_CONFIG
    wait 10
    bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt=7 -m=2 -b="$BENCHMARK" -folder_name="$FOLDER_NAME/2-7-$f" -na=$PATH_TO_CONFIG
    wait 10
done 



BASELINE_FOLDER=/home/snazk/PerfVar/Repo/New/SYCL-OMP-PerfVar/benchmarks/logs/BaselinesNbody/TP/nbody-omp
python3 ./traces_to_noise_config.py $BASELINE_FOLDER -o hybrid-config.json -w main

PATH_TO_CONFIG=/home/snazk/PerfVar/Repo/New/SYCL-OMP-PerfVar/scripts/hybrid-config.json
FOLDER_NAME=CompareNbody-Comb-TP-057
BENCHMARK="0"

for f in {0..1}
do
    bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt=6 -m=0 -b="$BENCHMARK" -folder_name="$FOLDER_NAME/0-6-$f" -na=$PATH_TO_CONFIG
    wait 10

    for i in {0..2}
    do
        k=8
        bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt="$k" -m="$i" -b="$BENCHMARK" -folder_name="$FOLDER_NAME/$i-$k-$f" -na=$PATH_TO_CONFIG
        wait 10
    done

    bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt=7 -m=0 -b="$BENCHMARK" -folder_name="$FOLDER_NAME/0-7-$f" -na=$PATH_TO_CONFIG
    wait 10
    bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt=7 -m=2 -b="$BENCHMARK" -folder_name="$FOLDER_NAME/2-7-$f" -na=$PATH_TO_CONFIG
    wait 10
done 


BASELINE_FOLDER=/home/snazk/PerfVar/Repo/New/SYCL-OMP-PerfVar/benchmarks/logs/BaselinesBabelstream/Roam/babelstream-omp
python3 ./traces_to_noise_config.py $BASELINE_FOLDER -o hybrid-config.json -w main

PATH_TO_CONFIG=/home/snazk/PerfVar/Repo/New/SYCL-OMP-PerfVar/scripts/hybrid-config.json
FOLDER_NAME=CompareBabelstream-Comb-Roam-195
BENCHMARK="1"
for f in {0..1}
do
    bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt=6 -m=0 -b="$BENCHMARK" -folder_name="$FOLDER_NAME/0-6-$f" -na=$PATH_TO_CONFIG
    wait 10

    for i in {0..2}
    do
        k=8
        bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt="$k" -m="$i" -b="$BENCHMARK" -folder_name="$FOLDER_NAME/$i-$k-$f" -na=$PATH_TO_CONFIG
        wait 10
    done

    bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt=7 -m=0 -b="$BENCHMARK" -folder_name="$FOLDER_NAME/0-7-$f" -na=$PATH_TO_CONFIG
    wait 10
    bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt=7 -m=2 -b="$BENCHMARK" -folder_name="$FOLDER_NAME/2-7-$f" -na=$PATH_TO_CONFIG
    wait 10
done 















BASELINE_FOLDER=/home/snazk/PerfVar/Repo/New/SYCL-OMP-PerfVar/benchmarks/logs/BaselinesMiniFE/RoamHK/miniFE-omp
python3 ./traces_to_noise_config.py $BASELINE_FOLDER -o hybrid-config.json -w miniFE.x

PATH_TO_CONFIG=/home/snazk/PerfVar/Repo/New/SYCL-OMP-PerfVar/scripts/hybrid-config.json
FOLDER_NAME=CompareMiniFE-Comb-RoamHK-12
BENCHMARK="2"

for f in {0..1}
do
    bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt=6 -m=0 -b="$BENCHMARK" -folder_name="$FOLDER_NAME/0-6-$f" -na=$PATH_TO_CONFIG
    wait 10

    for i in {0..2}
    do
        k=8
        bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt="$k" -m="$i" -b="$BENCHMARK" -folder_name="$FOLDER_NAME/$i-$k-$f" -na=$PATH_TO_CONFIG
        wait 10
    done

    bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt=7 -m=0 -b="$BENCHMARK" -folder_name="$FOLDER_NAME/0-7-$f" -na=$PATH_TO_CONFIG
    wait 10
    bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt=7 -m=2 -b="$BENCHMARK" -folder_name="$FOLDER_NAME/2-7-$f" -na=$PATH_TO_CONFIG
    wait 10
done 

BASELINE_FOLDER=/home/snazk/PerfVar/Repo/New/SYCL-OMP-PerfVar/benchmarks/logs/BaselinesNbody/TPHK/nbody-omp
python3 ./traces_to_noise_config.py $BASELINE_FOLDER -o hybrid-config.json -w main

PATH_TO_CONFIG=/home/snazk/PerfVar/Repo/New/SYCL-OMP-PerfVar/scripts/hybrid-config.json
FOLDER_NAME=CompareNbody-Comb-TPHK-054
BENCHMARK="0"

for f in {0..1}
do
    bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt=6 -m=0 -b="$BENCHMARK" -folder_name="$FOLDER_NAME/0-6-$f" -na=$PATH_TO_CONFIG
    wait 10

    for i in {0..2}
    do
        k=8
        bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt="$k" -m="$i" -b="$BENCHMARK" -folder_name="$FOLDER_NAME/$i-$k-$f" -na=$PATH_TO_CONFIG
        wait 10
    done

    bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt=7 -m=0 -b="$BENCHMARK" -folder_name="$FOLDER_NAME/0-7-$f" -na=$PATH_TO_CONFIG
    wait 10
    bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt=7 -m=2 -b="$BENCHMARK" -folder_name="$FOLDER_NAME/2-7-$f" -na=$PATH_TO_CONFIG
    wait 10
done 

BASELINE_FOLDER=/home/snazk/PerfVar/Repo/New/SYCL-OMP-PerfVar/benchmarks/logs/BaselinesBabelstream/Roam/babelstream-sycl
python3 ./traces_to_noise_config.py $BASELINE_FOLDER -o hybrid-config.json -w main

PATH_TO_CONFIG=/home/snazk/PerfVar/Repo/New/SYCL-OMP-PerfVar/scripts/hybrid-config.json
FOLDER_NAME=CompareBabelstream-Comb-Roam-22
BENCHMARK="1"
for f in {0..1}
do
    bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt=6 -m=0 -b="$BENCHMARK" -folder_name="$FOLDER_NAME/0-6-$f" -na=$PATH_TO_CONFIG
    wait 10

    for i in {0..2}
    do
        k=8
        bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt="$k" -m="$i" -b="$BENCHMARK" -folder_name="$FOLDER_NAME/$i-$k-$f" -na=$PATH_TO_CONFIG
        wait 10
    done

    bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt=7 -m=0 -b="$BENCHMARK" -folder_name="$FOLDER_NAME/0-7-$f" -na=$PATH_TO_CONFIG
    wait 10
    bash ./Benchmark.sh -f=$f -i="$ITER" -t=0 -mt=7 -m=2 -b="$BENCHMARK" -folder_name="$FOLDER_NAME/2-7-$f" -na=$PATH_TO_CONFIG
    wait 10
done 
