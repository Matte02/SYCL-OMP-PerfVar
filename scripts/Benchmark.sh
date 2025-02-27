#!/bin/bash

# Configuration
SYSTEM="Chris"  # System name
OSNOISEPATH="/sys/kernel/tracing"  # Path to osnoise tracer
CURPATH="$PWD"  # Current working directory
ITER=1  # Number of iterations per benchmark
TRACE=1  # Enable/disable tracing (1 = enabled, 0 = disabled)
INJECT_NOISE_VALUE="yes"  # Enable/disable noise injection (yes/no)


# Benchmark parameters (default values)
#NBODY_PARAMS="10000 10000"
NBODY_PARAMS="10000 100"
#MINIFE_PARAMS="-nx 256 -ny 256 -nz 128"
BABELSTREAM_PARAMS="-s 33554432 -n 10"
#BABELSTREAM_PARAMS="-s 33554432"
MINIFE_PARAMS="-nx 128 -ny 128 -nz 128"

# Path to benchmarks
benchpath="$CURPATH/../benchmarks"
benchtime=$(date '+%d-%m-%Y-%H:%M:%S')
logpath="$benchpath/logs/benchrun-$benchtime"
mkdir -p "$logpath"

# Noise injection configuration
if [ "$INJECT_NOISE_VALUE" = "yes" ]; then
    echo "Noise injection is enabled. Using noise injection parameters."
    key_count=$(jq 'length' ../noiseinjector/noise_config.json)
    benches=("nbody")
    benchparameters=("$NBODY_PARAMS $key_count")
    binname=("main")
    frameworks=("omp" "sycl")
    #This should ensure that we are able to reach 100% utilization for the realtime processes
    echo 1000000 > /proc/sys/kernel/sched_rt_runtime_us

    noise_config_file="$CURPATH/../noiseinjector/noise_config.json"
    echo "Copy Noise config file at: $noise_config_file to $logpath"
    cp  "$noise_config_file" "$logpath/"
else
    echo "Noise injection is disabled. Using default parameters."
    benches=("nbody" "babelstream" "miniFE")
    benchparameters=("$NBODY_PARAMS" "$BABELSTREAM_PARAMS" "$MINIFE_PARAMS")
    makefilepath=("." "." "src")  # Path extensions for Makefiles
    binname=("main" "main" "miniFE.x")  # Binary names
    frameworks=("omp" "sycl")
fi

# Source Intel OneAPI environment
source /opt/intel/oneapi/setvars.sh

# Setup tracer
echo "osnoise" > "$OSNOISEPATH/current_tracer"
echo "NO_OSNOISE_WORKLOAD" > "$OSNOISEPATH/osnoise/options"
echo > "$OSNOISEPATH/set_event"
echo "osnoise" > "$OSNOISEPATH/set_event"
echo "mono_raw" > "$OSNOISEPATH/trace_clock"

# TODO: Make the common makefile here

# Path to benchmarks
benchpath="$CURPATH/../benchmarks"
benchtime=$(date '+%d-%m-%Y-%H:%M:%S')

#Loop thorugh all benches, versions, and iterations
benchidx=-1
for bench in ${benches[@]}; do
    benchidx=$((benchidx+1))
    for framework in ${frameworks[@]}; do
        curbench="$bench-$framework"
        cd "$benchpath/$curbench/${makefilepath[$benchidx]}" || exit 1

        # Clean and build the benchmark
        make clean
        make CC=icpx DEVICE=cpu GPU=no INJECT_NOISE=$INJECT_NOISE_VALUE

        #Select Params
        params=${benchparameters[$benchidx]}

        # Create log directory
        logpath="$benchpath/logs/benchrun-$benchtime/$curbench"
        mkdir -p "$logpath"
        echo "Log path: $logpath"
        echo "Start: $curbench"

        for ((i=1; i<=$ITER; i++)) do
            TRACECOUNT=$i
            touch "$logpath/$curbench-$TRACECOUNT-$SYSTEM.benchout"

            # Enable tracing if specified
            if [ $TRACE -eq 1 ]; then
                touch "$logpath/$curbench-$TRACECOUNT-$SYSTEM.trace"
                echo > "$OSNOISEPATH/trace"
                echo 1 > "$OSNOISEPATH/tracing_on"
                sleep 1  # Allow tracer warmup
            fi

            echo $i
            # Run the benchmark
            binary="${binname[$benchidx]}"
            time ./"$binary" $params > "$logpath/$curbench-$TRACECOUNT-$SYSTEM.benchout" 2>&1 &
            benchmark_pid=$!  # Save the PID of the benchmark process

            if [ "$INJECT_NOISE_VALUE" = "yes" ]; then
                #Allow the workload to reach barrier 
                sleep 1
                # Run noise injection script in the background
                cd "$CURPATH" || exit 1
                output_file="$logpath/$curbench-$SYSTEM.noiseout" 2>&1
                python3 "$CURPATH/run_noise.py" --verbose --rebuild --debug >> $output_file&
                noise_pid=$!
                cd "$benchpath/$curbench/${makefilepath[$benchidx]}" || exit 1
            fi
            #Wait for all child processes to finish
            wait  $benchmark_pid

            if [ "$INJECT_NOISE_VALUE" = "yes" ]; then
                kill -SIGTERM $noise_pid
                wait $noise_pid
            fi
            # Disable tracing if specified
            if [ $TRACE -eq 1 ]; then
                echo 0 > "$OSNOISEPATH/tracing_on"
                sleep 1
                cat "$OSNOISEPATH/trace" > "$logpath/$curbench-$TRACECOUNT-$SYSTEM.trace"
            fi
            
            # Save benchmark output
            echo "Input params: $params" >> "$logpath/$curbench-$TRACECOUNT-$SYSTEM.benchout"
            echo "Noise injector was enabled? A: $INJECT_NOISE_VALUE" >> "$logpath/$curbench-$TRACECOUNT-$SYSTEM.benchout"
        done
        
        echo "End: $curbench"
    done
done

echo "Benchmarking done"

