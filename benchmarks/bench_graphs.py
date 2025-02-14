import os 
from os import walk
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
import numpy as np
import sys
import locale

#Usage: Arg 1 contains the path to the folder where folders of benchmark outputs are stored
def main():
    if not os.path.exists(sys.argv[1]):
        print('Arg not a path')
        return
    
    benches = os.listdir(sys.argv[1])
    for bench in benches:
        if not os.path.isdir(bench):
            continue
        
        benchpath=os.path.normpath(sys.argv[1])+'/'+os.path.normpath(bench)
        files = []

        for (dirpath, dirnames, filenames) in walk(benchpath):
            for file in filenames:
                if file.endswith(".benchout"):
                    files.append(file)
            break 

        if len(files)==0:
            break

        exectimes = []

        for file in files:
            with open(benchpath+"/"+file, "r") as files:
                first = files.readline()
                for last in files: pass

            exectimes.append(float(locale.delocalize(last[0:(len(last)-1)])))
            
        exectimes.sort()
        print(len(exectimes))
        avgexectime = sum(exectimes)/len(exectimes)
        normexectimes = list(map(lambda x: x/avgexectime, exectimes))


        fig, axs = plt.subplots()
        axs.set_ylabel('Execution time (normalized)')
        axs.set_xlabel(bench)
        boxplot = axs.boxplot([normexectimes]) 
        plt.xticks([])
        plt.savefig(benchpath+'.png')

        fig, axs = plt.subplots()

        axs.set_ylabel('Execution time (s)')
        axs.set_xlabel(bench)
        boxplot = axs.boxplot([exectimes]) 
        plt.xticks([])
        plt.savefig(benchpath+'-sec.png')

        
    else:
        print("No benchpath specified")

if __name__ == "__main__":
    main()

    
    
    



