import os 
from os import walk
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
import numpy as np
import sys
import locale
import re
from multiprocessing import Pool
import json

#Usage: Arg 1 contains the path to the trace file. Arg 2 contains workload name eg "main"
def main():
    if not os.path.isfile(sys.argv[1]+".trace") & os.path.isfile(sys.argv[1]+".benchout"):
        print('Arg not a path to file')
        return
    
    if len(sys.argv) < 3:
        print('Workload task name not specified')
        workloadtaskname=""
    else: 
        workloadtaskname=sys.argv[2] 

    
    tracepath=os.path.normpath(sys.argv[1])



    #Todo fetch correct info from .benchout
    #synchstart = 0
    #startclockre = re.compile("Start time: [0-9.]*")
    #with open(tracepath+".benchout", "r") as lines:
    #    for line in lines:
    #        synchstart = startclockre.match(line)
    #        if synchstart != None:
    #            synchstart = synchstart.group(0)[12:]
    #            break
                

    #Dict(CPU,Dict(task,[(start,duration)]))
    cpudict: dict[int, dict[str, list[(int, int)]]]#= dict({'NULL': dict({'NULL': []})})
    cpudict = dict()
    commentre = re.compile("#")
    starttlcre = re.compile("start [0-9.]*")
    durationtlcre = re.compile("duration [0-9]*")
    cpure = re.compile("\\[[0-9]{3}\\]")
    #5258.924435: irq_noise: local_timer:236 start
    #timestampre = re.compile("[0-9]{4}\\.[0-9]*:")
    taskre = re.compile("noise: .*:")

    #Fill cpu dictionary
    with open(tracepath+".trace", "r") as lines:
        for line in lines:
            if commentre.match(line) != None:
                continue
            cpu = cpure.search(line)
            cpu = int(cpu.group(0)[1:len(cpu.group(0))-1])
            start = starttlcre.search(line)
            start = start.group(0)[6:]
            tmp = start.split(".")
            start = int(tmp[0]+tmp[1])

            duration = durationtlcre.search(line)
            duration = int(duration.group(0)[9:])
            #timestamp = timestampre.search(line)
            #timestamp = timestamp.group(0)[:len(timestamp.group(0))-1]
            task = taskre.search(line)

            if task == None:
                task = "NMI"
            else:
                task = task.group(0)[7:len(task.group(0))-1].strip()

            cpuoldval = cpudict.get(cpu)
            if cpuoldval != None:
                taskoldval = cpuoldval.get(task)        
                if taskoldval != None:
                    taskoldval.append((start,duration))
                    cpuoldval[task] = taskoldval
                else: 
                    cpuoldval[task] = [(start,duration)]

                cpudict[cpu] = cpuoldval
            else:
                cpudict[cpu] = dict({task: [(start,duration)]})
    
    #Sort all tasks based on start time
    pool = Pool()
    for cpu, tasks in cpudict.items():
        cpudict[cpu] = pool.map(sort_task_start, tasks.items())

    #Seperate workload from noise and remove unnecessary noise information (taskname)
    noisedict = dict()
    workloadexec = []
    for cpu, tasks in cpudict.items():
        noise = []
        for task, timinglist in tasks:
            if task != workloadtaskname:
                noise.extend(timinglist)
            else:
                workloadexec.extend(timinglist)
        noise = sorted(noise, key=lambda tup: tup[0])
        noisedict[cpu] = noise
    
    workloadexec = sorted(workloadexec, key=lambda tup: tup[0])

    #Tries to align mono_raw and osnoise ("tlc") start clock 
    syncstartdiff = workloadexec[0][0]

    #Combine several preempting noises into one consecutive noise
    for cpu, noises in noisedict.items():
        combinednoises = list()
        nextduration = -1
        nextstart = -1
        for noise in noises:
            print("Combine?")
            print(nextstart)
            print(nextduration)
            print(noise)
            #Make the start of the workload be time instant 0
            noise = noise[0]-syncstartdiff, noise[1]
            #Remove noises started before starting point
            if noise[0] < 0: 
                continue
            #First noise
            if nextstart == -1:
                nextstart = noise[0]
                nextduration = noise[1]
            else: 
                end = nextstart + noise[1]
                #Check if starttime is during an execution of another noise. If yes, combine.
                if end >= noise[0]:
                    print("Combine")
                    nextduration = nextduration + noise[1]
                else:
                    combinednoises.append((nextstart, nextduration))
                    nextstart = noise[0]
                    nextduration = noise[1]

        combinednoises.append((nextstart, nextduration))
        noisedict[cpu] = combinednoises 

    #Write output to json
    json_string = json.dumps(noisedict, indent=4) 
    with open("noise_config.json", "w") as f:
        f.write(json_string) 


def sort_task_start(task):
    return (task[0], sorted(task[1], key=lambda tup: tup[0]))



if __name__ == "__main__":
    main()

    
    
    



