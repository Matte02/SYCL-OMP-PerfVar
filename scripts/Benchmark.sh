#!/bin/bash

# Configuration
SYSTEM="matte"  # System name
OSNOISEPATH="/sys/kernel/tracing"  # Path to osnoise tracer
CURPATH="$PWD"  # Current working directory
ITER=1  # Number of iterations per benchmark
TRACE=1  # Enable/disable tracing (1 = enabled, 0 = disabled)
INJECT_NOISE_VALUE="no"  # Enable/disable noise injection (yes/no)


# Benchmark parameters (default values)
NBODY_PARAMS="10000 10000"
BABELSTREAM_PARAMS="-s 67108864"
MINIFE_PARAMS="-nx 256 -ny 256 -nz 128"

# Noise injection configuration
if [ "$INJECT_NOISE_VALUE" = "yes" ]; then
    echo "Noise injection is enabled. Using noise injection parameters."
    key_count=$(jq 'length' ../noiseinjector/noise_config.json)
    NBODY_PARAMS="10000 1000 $key_count"  # Update NBODY_PARAMS for noise injection
    benches=("nbody")
    benchparameters=("$NBODY_PARAMS")
    binname=("main")
    frameworks=("omp" "sycl")
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


# Path to benchmarks
benchpath="$CURPATH/../benchmarks"
benchcount=$(ls -1 "$benchpath/logs" | grep -E "benchrun-.*" | wc -l)

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
        logpath="$benchpath/logs/benchrun-$benchcount/$curbench"
        mkdir -p "$logpath"
        echo "Log path: $logpath"
        echo "Start: $curbench"

        for ((i=1; i<=$ITER; i++)) do
            TRACECOUNT="$(ls -1 $logpath | grep -E "$curbench.*$SYSTEM.*benchout" | wc -l)"
            touch "$logpath/$curbench-$TRACECOUNT-$SYSTEM.benchout"

            # Enable tracing if specified
            if [ $TRACE -eq 1 ]; then
                touch "$logpath/$curbench-$TRACECOUNT-$SYSTEM.trace"
                echo > "$OSNOISEPATH/trace"
                echo 1 > "$OSNOISEPATH/tracing_on"
                sleep 2  # Allow tracer warmup
            fi

            if [ "$INJECT_NOISE_VALUE" = "yes" ]; then
                # Run noise injection script in the background
                cd "$CURPATH" || exit 1
                python3 "$CURPATH/run_noise.py" --verbose --rebuild &
                noise_pid=$!
                cd "$benchpath/$curbench/${makefilepath[$benchidx]}" || exit 1
            fi

            # Run the benchmark
            binary="${binname[$benchidx]}"
            OUTPUT=$(TIMEFORMAT="%R"; { time ./"$binary" $params; } 2>&1)

            if [ "$INJECT_NOISE_VALUE" = "yes" ]; then
            benchmark_pid=$!  # Save the PID of the benchmark process
            wait $benchmark_pid $noise_pid
            fi
            
            # Disable tracing if specified
            if [ $TRACE -eq 1 ]; then
                echo 0 > "$OSNOISEPATH/tracing_on"
                sleep 2
                cat "$OSNOISEPATH/trace" > "$logpath/$curbench-$TRACECOUNT-$SYSTEM.trace"
            fi

            # Save benchmark output
            echo "Input params: $params" > "$logpath/$curbench-$TRACECOUNT-$SYSTEM.benchout"
            echo "$OUTPUT" >> "$logpath/$curbench-$TRACECOUNT-$SYSTEM.benchout"
        done
        
        echo "End: $curbench"
    done
done

echo "Benchmarking done"

