#System name
SYSTEM="Chris"
#Path to osnoise tracer
OSNOISEPATH="/sys/kernel/tracing"
#Path to folder where bench folder are located
CURPATH=$PWD
#Number of times to execute a bench
ITER=1
#Trace disabled(!1)/enabled(1)
TRACE=1

#Test Params
#NBODY_PARAMS="10000 200"
#BABELSTREAM_PARAMS=""
#MINIFE_PARAMS="-nx 128 -ny 128 -nz 128"

#~1 min per bench execution Params 
NBODY_PARAMS="10000 12000"
BABELSTREAM_PARAMS="-s 67108864"
MINIFE_PARAMS="-nx 256 -ny 256 -nz 128"

benches=("nbody" "babelstream" "miniFE")
benchparameters=("$NBODY_PARAMS" "$BABELSTREAM_PARAMS" "$MINIFE_PARAMS")
#Path extension to makefile and binary location if necessary
makefilepath=("." "." "src")
#Binary name
binname=("main" "main" "miniFE.x")
frameworks=("omp" "sycl")

source /opt/intel/oneapi/setvars.sh 

#Setup tracer
echo osnoise > "$OSNOISEPATH/current_tracer"
echo NO_OSNOISE_WORKLOAD > $OSNOISEPATH/osnoise/options
echo > "$OSNOISEPATH/set_event"
echo osnoise > "$OSNOISEPATH/set_event"

benchcount="$(ls -1 $CURPATH/logs | grep -E "benchrun-.*" | wc -l)"

#Loop thorugh all benches, versions, and iterations
benchidx=-1
for bench in ${benches[@]}; do
    benchidx=$((benchidx+1))
    for framework in ${frameworks[@]}; do
        curbench="$bench-$framework"
        cd $CURPATH/$curbench/${makefilepath[$benchidx]}
        params=${benchparameters[$benchidx]}

        make clean
        make CC=icpx DEVICE=cpu GPU=no #DEBUG=yes

        logpath="$CURPATH/logs/benchrun-$benchcount/$curbench"
        mkdir -p $logpath

        echo "Start: $bench-$framework"

        for ((i=1; i<=$ITER; i++))
        do
            TRACECOUNT="$(ls -1 $logpath | grep -E "$curbench.*$SYSTEM.*benchout" | wc -l)"
            touch "$logpath/$curbench-$TRACECOUNT-$SYSTEM.benchout"

            if [ $TRACE -eq 1 ]
            then
                touch "$logpath/$curbench-$TRACECOUNT-$SYSTEM.trace"
                echo > "$OSNOISEPATH/trace"
                echo 1 > "$OSNOISEPATH/tracing_on"
                #Sleep to allow for tracer warmup. Neccessary?
                sleep 2
            fi
            binary=${binname[$benchidx]}
            #OUTPUT="$(time ./$binary $params)"
            OUTPUT=$( TIMEFORMAT="%R"; { time ./$binary $params; } 2>&1 )

            if [ $TRACE -eq 1 ]
            then
                echo 0 > "$OSNOISEPATH/tracing_on"
                sleep 2
                cat "$OSNOISEPATH/trace" > "$logpath/$curbench-$TRACECOUNT-$SYSTEM.trace"
            fi

            echo "Input params: $params" > "$logpath/$curbench-$TRACECOUNT-$SYSTEM.benchout"
            echo "$OUTPUT" >> "$logpath/$curbench-$TRACECOUNT-$SYSTEM.benchout"
        done
        
        echo "End: $bench-$framework"
    done
done

echo "Benchmarking done"

