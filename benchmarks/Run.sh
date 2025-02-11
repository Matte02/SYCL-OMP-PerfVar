SYSTEM="Chris"
BENCHPATH="$PWD/$1"
CURPATH=$PWD
export OMP_NUM_THREADS=8

source /opt/intel/oneapi/setvars.sh 
#export OMP_NUM_THREADS=8

cd "$BENCHPATH"

make clean
make CC=icpx DEVICE=cpu GPU=no DEBUG=yes

mkdir "$CURPATH/logs"
TRACECOUNT="$(ls -1 "$CURPATH/logs/" | grep -E "$1.*$SYSTEM.*runout" | wc -l)"
touch "$CURPATH/logs/$1-$TRACECOUNT-$SYSTEM.runout"

#nice --20 ./main $2
sleep 1
OUTPUT="$(./main $2)"

echo "Input params: $2" > "$CURPATH/logs/$1-$TRACECOUNT-$SYSTEM.runout"
echo "$OUTPUT" >> "$CURPATH/logs/$1-$TRACECOUNT-$SYSTEM.runout"
echo $OUTPUT



