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

#Usage: Arg 1 contains the path to the trace file
def main():
    if not os.path.isfile(sys.argv[1]+".trace") & os.path.isfile(sys.argv[1]+".benchout"):
        print('Arg not a path to file')
        return
    
    tracepath=os.path.normpath(sys.argv[1])



    #Todo fetch correct start form benchout
    synchStart = 0
    #with open(tracepath+".benchout", "r") as lines:
    #    for line in lines:
                

    #Dict(CPU,Dict(task,[(start,duration)]))
    cpudict: dict[int, dict[str, list[(int, int)]]]#= dict({'NULL': dict({'NULL': []})})
    cpudict = dict()
    commentre = re.compile("#")
    starttlcre = re.compile("start [0-9.]*")
    durationtlcre = re.compile("duration [0-9]*")
    #numberre = re.compile("[0-9.]*")
    cpure = re.compile("\\[[0-9]{3}\\]")
    #5258.924435: irq_noise: local_timer:236 start
    endtimestampre = re.compile("[0-9]{4}\\.[0-9]*:")
    taskre = re.compile("noise: .*:")

    #Fill cpu dictionary
    with open(tracepath+".trace", "r") as lines:
        for line in lines:
            if commentre.match(line) != None:
                continue
            cpu = cpure.search(line)
            #print(cpu.group(0))
            cpu = int(cpu.group(0)[1:len(cpu.group(0))-1])
            print(cpu)
            start = starttlcre.search(line)
            start = start.group(0)[6:]
            duration = durationtlcre.search(line)
            duration = duration.group(0)[9:]
            endtime = endtimestampre.search(line)
            endtime = endtime.group(0)[:len(endtime.group(0))-1]
            task = taskre.search(line)
            #print(line)
            #print(task)
            if task == None:
                task = "NMI"
            else:
                task = task.group(0)[7:len(task.group(0))-1]

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
    
    pool = Pool()
    for cpu, tasks in cpudict.items():
        #print(tasks.items())
        cpudict[cpu] = pool.map(sort_task_start, tasks.items())

    json_string = json.dumps(cpudict, indent=4) 
    
    with open("noise_config.json", "w") as f:
        f.write(json_string) 
    #print(json_string)
    #print(cpudict)
    


def sort_task_start(task):
    return (task[0], sorted(task[1], key=lambda tup: tup[0]))



if __name__ == "__main__":
    main()

    
    
    



