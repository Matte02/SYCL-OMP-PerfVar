SYSTEM="Chris"
OSNOISEPATH="/sys/kernel/tracing"
BENCHPATH="$PWD/$1"
CURPATH=$PWD
export OMP_NUM_THREADS=8
#export OMP_PLACES="threads" 
#export OMP_PROC_BIND="true" 

source /opt/intel/oneapi/setvars.sh 

cd "$BENCHPATH"

echo osnoise > "$OSNOISEPATH/current_tracer"

#echo NO_OSNOISE_WORKLOAD > $OSNOISEPATH/osnoise/options
if [ $3 == 1 ]; then
    echo OSNOISE_WORKLOAD > $OSNOISEPATH/osnoise/options
else
    echo NO_OSNOISE_WORKLOAD > $OSNOISEPATH/osnoise/options
fi

echo > "$OSNOISEPATH/set_event"
echo osnoise > "$OSNOISEPATH/set_event"
#echo osnoise >> "$OSNOISEPATH/set_event"
#echo sched >> "$OSNOISEPATH/set_event"
#echo *:* > "$OSNOISEPATH/set_event"
make clean
make CC=icpx DEVICE=cpu GPU=no #DEBUG=yes

mkdir "$CURPATH/logs"
TRACECOUNT="$(ls -1 "$CURPATH/logs/" | grep -E "$1.*$SYSTEM.*trace" | wc -l)"
touch "$CURPATH/logs/$1-$TRACECOUNT-$SYSTEM.trace"
touch "$CURPATH/logs/$1-$TRACECOUNT-$SYSTEM.output"


echo > "$OSNOISEPATH/trace"
echo 1 > "$OSNOISEPATH/tracing_on"

#nice --20 ./main $2
sleep 1
OUTPUT="$(./main $2)"

echo 0 > "$OSNOISEPATH/tracing_on"

echo "Input params: $2" > "$CURPATH/logs/$1-$TRACECOUNT-$SYSTEM.output"
echo "$OUTPUT" >> "$CURPATH/logs/$1-$TRACECOUNT-$SYSTEM.output"
cat "$OSNOISEPATH/trace" > "$CURPATH/logs/$1-$TRACECOUNT-$SYSTEM.trace"
echo $OUTPUT

