#!/bin/bash

# Configuration
SYSTEM="chris"  # System name
OSNOISEPATH="/sys/kernel/tracing"  # Path to osnoise tracer
CURPATH="$PWD"  # Current working directory
ITER=5  # Number of iterations per benchmark
TRACE=1  # Enable/disable tracing (1 = enabled, 0 = disabled)
INJECT_NOISE_VALUE="no"  # Enable/disable noise injection (yes/no)
NOISE_INJECT_ON_ANY_CORE="no" # Enable/disable migration of noise injections processes during noise injection
THREADS="$(nproc)"     # Sets the amount of threads that will be utilized by the workload
THREAD_PINNING="no" # Enable/disable thread pinning (yes/no), warning: miniFE sycl does not perform with both OMP and DPCPP envars
HOUSEHOLDING="no" # Enable/disable thread pinning (yes/no)
key_count=$(jq 'length' ../noiseinjector/noise_config.json)


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
logfolderpath="$benchpath/logs/benchrun-$benchtime"
mkdir -p "$logfolderpath"

graphfolder="$logfolderpath/graphs"
mkdir -p "$graphfolder"

#Default parameters
benches=("nbody" "babelstream" "miniFE")
benchparameters=("$NBODY_PARAMS" "$BABELSTREAM_PARAMS" "$MINIFE_PARAMS")
makefilepath=("." "." "src")  # Path extensions for Makefiles
binname=("main" "main" "miniFE.x")  # Binary names
#benches=("nbody" "babelstream")
#benchparameters=("$NBODY_PARAMS" "$BABELSTREAM_PARAMS")
#makefilepath=("." ".")  # Path extensions for Makefiles
#binname=("main" "main")  # Binary names
frameworks=("omp" "sycl")

#Handle arguments
for i in "$@"; do
  case $i in
    -i=*)
        ITER="${i#*=}"
        shift # past argument=value
        ;;
    -t=*)
        TRACE="${i#*=}"
        shift # past argument=value
        ;;
    -na=*)
        INJECT_NOISE_VALUE="yes"
        NOISE_INJECT_ON_ANY_CORE="yes"
        noise_config_file="${i#*=}"
        echo "Copy Noise config file at: $noise_config_file to $logfolderpath"
        cp  "$noise_config_file" "$logfolderpath/"
        key_count=$(jq 'length' $logfolderpath/noise_config.json)
        for k in "${!benchparameters[@]}"; do
            benchparameters[$k]="${benchparameters[$k]} $key_count"
        done
        #This should ensure that we are able to reach 100% utilization for the realtime processes
        echo 1000000 > /proc/sys/kernel/sched_rt_runtime_us
        # TODO Fix to allow different noises for different frameworks.
        python3 "$CURPATH/noise_config_graphs.py" "${i#*=}" "$graphfolder/injected_noise"
        echo "Running: $CURPATH/noise_config_graphs.py" "${i#*=}" "$graphfolder/injected_noise"
        shift # past argument=value
        ;;
    -n=*)
        INJECT_NOISE_VALUE="yes"
        NOISE_INJECT_ON_ANY_CORE="no"
        noise_config_file="${i#*=}"
        echo "Copy Noise config file at: $noise_config_file to $logfolderpath"
        cp  "$noise_config_file" "$logfolderpath/"
        key_count=$(jq 'length' $logfolderpath/noise_config.json)
        for k in "${!benchparameters[@]}"; do
            benchparameters[$k]="${benchparameters[$k]} $key_count"
        done
        #This should ensure that we are able to reach 100% utilization for the realtime processes
        echo 1000000 > /proc/sys/kernel/sched_rt_runtime_us
        # TODO Allow different noises for different frameworks.
        python3 "$CURPATH/noise_config_graphs.py" "${i#*=}" "$graphfolder/injected_noise"
        echo "Running: $CURPATH/noise_config_graphs.py" "${i#*=}" "$graphfolder/injected_noise"
        shift # past argument=value
        ;;
    -b=*)
        benches=( ${benches["${i#*=}"]} )
        benchparameters=( "${benchparameters["${i#*=}"]}" )
        makefilepath=( "${makefilepath["${i#*=}"]}" )  # Path extensions for Makefiles
        binname=( "${binname["${i#*=}"]}" )  # Binary names
        shift # past argument=value
        ;;
    -f=*)
        frameworks=( "${frameworks["${i#*=}"]}" )
        shift # past argument=value
        ;;
    -mt=*)
        THREADS="${i#*=}"
        echo "Threads to use set to $THREADS"
        shift # past argument=value
        ;;
    -m=*)
        case "${i#*=}" in
            "0")
                THREAD_PINNING="no"
                HOUSEHOLDING="no"
                echo "No mitigation strategy"
                ;;
            "1")
                THREAD_PINNING="yes"
                HOUSEHOLDING="no"
                echo "Threadpinning enabled"
                ;;
            "2")
                THREAD_PINNING="yes"
                HOUSEHOLDING="yes"
                echo "Threadpinning + housekeeping enabled"
                ;;
            *)
                ;;
        esac
        shift # past argument=value
        ;;
    -*|--*)
        echo "Unknown option $i"
        exit 1
        ;;
    *)
        ;;
  esac
done

# Source Intel OneAPI environment
source /opt/intel/oneapi/setvars.sh

# Setup tracer
echo "osnoise" > "$OSNOISEPATH/current_tracer"
echo "NO_OSNOISE_WORKLOAD" > "$OSNOISEPATH/osnoise/options"
echo > "$OSNOISEPATH/set_event"
echo "osnoise" > "$OSNOISEPATH/set_event"
echo "mono_raw" > "$OSNOISEPATH/trace_clock"

# Setup environment variables
places="threads"
proc_bind="false" # If proc_bind is set to false for OMP env var then threads 
                  # are distributed randomly even though places is explicitly set 

if [ "$THREAD_PINNING" = "yes" ]; then
    proc_bind="spread"
    export DPCPP_CPU_CU_AFFINITY=$proc_bind
    if [ "$HOUSEHOLDING" = "yes" ]; then
        housholding_cpus=$((threads / 8)) #12.5% of available cpus
        places="{0}:$(($THREADS - $housholding_cpus)):1"
        $THREADS=$(($THREADS - $housholding_cpus))
    fi
fi

export OMP_NUM_THREADS=$THREADS
export OMP_PLACES=$places
export OMP_PROC_BIND=$proc_bind

export DPCPP_CPU_NUM_CUS=$THREADS
export DPCPP_CPU_PLACES=$places


make -C ../noiseinjector clean
make -C ../noiseinjector
make -C ../common clean
make -C ../common

# Define a cleanup function
cleanup() {
    echo "Cleaning up..."
    if [ -n "$noise_pid" ]; then
        echo "Killing noise injection process with PID: $noise_pid"
        kill -SIGTERM "$noise_pid"
        wait "$noise_pid"  # Wait for the noise process to terminate
    fi
    exit 0
}

# Trap SIGINT (Ctrl + C) signal
trap cleanup SIGINT
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
        logpath="$logfolderpath/$curbench"
        mkdir -p "$logpath"
        echo "Log path: $logpath"
        binary="${binname[$benchidx]}"
        
        if [ "$INJECT_NOISE_VALUE" != "yes" ]; then
            echo "Warmup: $curbench"
            ./"$binary" $params >/dev/null 2>&1
            ./"$binary" $params >/dev/null 2>&1
            ./"$binary" $params >/dev/null 2>&1
        fi

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
            time ./"$binary" $params > "$logpath/$curbench-$TRACECOUNT-$SYSTEM.benchout" 2>&1 &
            benchmark_pid=$!  # Save the PID of the benchmark process

            if [ "$INJECT_NOISE_VALUE" = "yes" ]; then
                # Allow the workload to reach barrier 
                sleep 1
                # Run noise injection script in the background
                cd "$CURPATH" || exit 1
                output_file="$logpath/$curbench-$SYSTEM.noiseout" 2>&1
                if [ "$NOISE_INJECT_ON_ANY_CORE" = "yes" ]; then
                    python3 "$CURPATH/run_noise.py" --verbose --debug --any-core --json-file "$logfolderpath/noise_config.json" >> $output_file&
                else
                    python3 "$CURPATH/run_noise.py" --verbose --debug --json-file "$logfolderpath/noise_config.json" >> $output_file&
                fi
                noise_pid=$!
                cd "$benchpath/$curbench/${makefilepath[$benchidx]}" || exit 1
            fi
            #Wait for all child processes to finish
            wait  $benchmark_pid

            if [ "$INJECT_NOISE_VALUE" = "yes" ]; then
                # End noise injection
                kill -SIGTERM $noise_pid
                wait $noise_pid
            fi

            # Disable tracing if specified
            if [ $TRACE -eq 1 ]; then
                # Sleep to allow for cooldown period where noises stretching past workload end are captured
                sleep 1
                # Turn off tracing
                echo 0 > "$OSNOISEPATH/tracing_on"
                # Sleep to guarante tracing being turned of before starting next benchmark iteration
                sleep 1
                # Save trace
                cat "$OSNOISEPATH/trace" > "$logpath/$curbench-$TRACECOUNT-$SYSTEM.trace"
            fi
            
            # Save benchmark output
            echo "Input params: $params" >> "$logpath/$curbench-$TRACECOUNT-$SYSTEM.benchout"
            echo "Noise injector was enabled? A: $INJECT_NOISE_VALUE" >> "$logpath/$curbench-$TRACECOUNT-$SYSTEM.benchout"
        done
        #Create noise graphs
        if [ "$INJECT_NOISE_VALUE" = "yes" ]; then
            python3 "$CURPATH/noise_graphs.py" "$logpath" "$graphfolder/observed_noise"
        #Generate noise injection configuration
        elif [ $TRACE -eq 1 ]; then
            cd "$CURPATH" || exit 1
            python3 "$CURPATH/traces_to_noise_config.py" "$logpath"
            mv "$CURPATH/noise_config.json" "$logpath" 
            cd "$benchpath/$curbench/${makefilepath[$benchidx]}" || exit 1
        fi
        echo "End: $curbench"
    done
done
mkdir -p "$graphfolder/performance"
echo "Running: $CURPATH/bench_graphs.py" "$logfolderpath" "$graphfolder/performance"
python3 "$CURPATH/bench_graphs.py" "$logfolderpath" "$graphfolder/performance"

echo "Benchmarking done"

