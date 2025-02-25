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
from functools import reduce

#Usage: Arg 1 contains the path to the trace folder. Arg 2 contains workload name eg "main"
def main(): 
    if len(sys.argv) < 3:
        print('Workload task name not specified. Defaulting to "main"')
        workloadtaskname="main"
    else: 
        workloadtaskname=sys.argv[2] 

    pool = Pool()
    
    tracepath=os.path.normpath(sys.argv[1])

    rawtracefiles = list()
    for file in os.listdir(tracepath):
        if file.endswith(".trace"): 
            rawtracefiles.append(file)

    rawtracefiles = sorted(rawtracefiles, key=lambda file: int(file.split("-")[2]))

    #Contains list of all traces cpudict with duration attached
    tracelist: list[(dict[int, dict[str, list[(int, int)]]], int)]
    tracelist = list()
    print(rawtracefiles)
    tracelist = pool.map(getcpudict, rawtracefiles)

    print("Number of traces:")
    print(len(tracelist))

    #Fetch worst case trace
    worsttrace = max(tracelist, key=lambda x: int(x[1]))

    print("Worst trace duration:")
    print(max(tracelist, key=lambda x: int(x[1]))[1])

    #Create average trace
    averagedict: dict[int, dict[str, list[(int, int)]]]
    averagedict = dict()
    #Gather all tasks
    for trace in tracelist:
        for cpu, tasks in trace[0].items():
            for task, timinglist in tasks.items():
                if not cpu in averagedict: 
                    averagedict[cpu] = dict()
                if not task in averagedict[cpu]:
                    averagedict[cpu][task] = list()
                averagedict[cpu][task] = averagedict[cpu][task]+timinglist

    
    #Set duration of task as average of all task on the same cpu
    for cpu, tasks in averagedict.items():
        for task, timinglist in tasks.items():
            averageduration = 0
            averageoccurencelist = list()
            i = 0
            
            for (timing, duration) in timinglist:
                averageduration += duration
                if i%len(tracelist) == 0:
                    averageoccurencelist.append((timing, duration))
                i += 1
            #Set average duration of task    
            averageduration = int(averageduration / len(timinglist))
            #Add average amount of occurences of task to list  
            averagedict[cpu][task] = map(lambda x: (x[0], averageduration), averageoccurencelist)

    #Try to remove average inherent noise from worst case trace
    worsttracenoinherent: dict[int, dict[str, list[(int, int)]]]
    worsttracenoinherent = dict()
    for cpu, tasks in worsttrace[0].items():
        for task, timinglist in tasks.items():
            for (timing, duration) in averagedict[cpu][task]:
                if len(worsttrace[0][cpu][task]) <= 0:
                    break
                closestidx = min(range(len(worsttrace[0][cpu][task])), key=lambda i: abs(worsttrace[0][cpu][task][i][1]-duration))
                print(closestidx)
                print(worsttrace[0][cpu][task][closestidx][1])
                if worsttrace[0][cpu][task][closestidx][1] - duration < 0: 
                    worsttrace[0][cpu][task] = worsttrace[0][cpu][task][:closestidx] + worsttrace[0][cpu][task][closestidx+1:]
                else: 
                    worsttrace[0][cpu][task][closestidx] = (worsttrace[0][cpu][task][closestidx][1], worsttrace[0][cpu][task][closestidx][1]-duration)
                   
    #Approximate average inherent noise has now been removed from worst case trace

    #Seperate workload from noise and remove unnecessary noise information (taskname)
    cpudict = worsttrace[0]
    noisedict = dict()
    workloadexec = []
    for cpu, tasks in cpudict.items():
        noise = []
        for task, timinglist in tasks.items():
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
            noise = (noise[0]-syncstartdiff, noise[1])
            #Remove noises started before starting point
            if noise[0] < 0: 
                continue
            #First noise
            if nextstart == -1:
                nextstart = noise[0]
                nextduration = noise[1]
            else: 
                #Check if starttime is during an execution of another noise. If yes, combine.
                if nextstart+nextduration >= noise[0]:
                    print("Combine")
                    nextduration += noise[1]
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




def getcpudict(file):
    tracepath=os.path.normpath(sys.argv[1])

    numberre = re.compile("[0-9]*")
    durationre = re.compile("Duration: [0-9.]*")
    commentre = re.compile("#")
    starttlcre = re.compile("start [0-9.]*")
    durationtlcre = re.compile("duration [0-9]*")
    cpure = re.compile("\\[[0-9]{3}\\]")
    #5258.924435: irq_noise: local_timer:236 start
    #timestampre = re.compile("[0-9]{4}\\.[0-9]*:")
    taskre = re.compile("noise: .*:")

    if file.endswith(".trace"): 
        #Fetch duration of workload
        with open(tracepath+"/"+file[:len(file)-6]+".benchout", "r") as lines:
            for line in lines:
                dur = durationre.match(line)
                if dur != None:
                    dur = dur.group(0)[10:]
                    dur = dur.split(".")
                    dur = int(dur[0]+dur[1])
                    break
                    

        #Dict(CPU,Dict(task,[(start,duration)]))
        cpudict: dict[int, dict[str, list[(int, int)]]]#= dict({'NULL': dict({'NULL': []})})
        cpudict = dict()

        #Fill cpu dictionary
        with open(tracepath+"/"+file, "r") as lines:
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
        for cpu, tasks in cpudict.items():
            for task, timinglist in tasks.items():
                cpudict[cpu][task] = sort_task_start((task, timinglist))[1]
            #cpudict[cpu] = pool.map(sort_task_start, tasks.items())
        return (cpudict, dur)

























#
    ##Seperate workload from noise and remove unnecessary noise information (taskname)
    #noisedict = dict()
    #workloadexec = []
    #for cpu, tasks in cpudict.items():
    #    noise = []
    #    for task, timinglist in tasks:
    #        if task != workloadtaskname:
    #            noise.extend(timinglist)
    #        else:
    #            workloadexec.extend(timinglist)
    #    noise = sorted(noise, key=lambda tup: tup[0])
    #    noisedict[cpu] = noise
    #
    #workloadexec = sorted(workloadexec, key=lambda tup: tup[0])
#
    ##Tries to align mono_raw and osnoise ("tlc") start clock 
    #syncstartdiff = workloadexec[0][0]
#
    ##Combine several preempting noises into one consecutive noise
    #for cpu, noises in noisedict.items():
    #    combinednoises = list()
    #    nextduration = -1
    #    nextstart = -1
    #    for noise in noises:
    #        print("Combine?")
    #        print(nextstart)
    #        print(nextduration)
    #        print(noise)
    #        #Make the start of the workload be time instant 0
    #        noise = (noise[0]-syncstartdiff, noise[1])
    #        #Remove noises started before starting point
    #        if noise[0] < 0: 
    #            continue
    #        #First noise
    #        if nextstart == -1:
    #            nextstart = noise[0]
    #            nextduration = noise[1]
    #        else: 
    #            #Check if starttime is during an execution of another noise. If yes, combine.
    #            if nextstart+nextduration >= noise[0]:
    #                print("Combine")
    #                nextduration += noise[1]
    #            else:
    #                combinednoises.append((nextstart, nextduration))
    #                nextstart = noise[0]
    #                nextduration = noise[1]
#
    #    combinednoises.append((nextstart, nextduration))
    #    noisedict[cpu] = combinednoises 
#
    ##Write output to json
#
    #
    #json_string = json.dumps(noisedict, indent=4) 
    #with open("noise_config.json", "w") as f:
    #    f.write(json_string) 

def sort_task_start(task):
    return (task[0], sorted(task[1], key=lambda tup: int(tup[0])))



if __name__ == "__main__":
    main()

    
    
    



