import os 
from os import walk
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
import numpy as np
import sys
import locale
import re

#Usage: Arg 1 contains the path to the folder where folders of benchmark outputs are stored
def main():
    if not os.path.exists(sys.argv[1]):
        print('Arg not a path')
        return
    
    benches = os.listdir(sys.argv[1])
    print(benches)

    for bench in benches:
        if not "sycl" in str(bench) and not "omp" in str(bench):
            continue

        if not os.path.isdir(os.path.normpath(sys.argv[1])+'/'+os.path.normpath(bench)):
            continue
        
        benchpath=os.path.normpath(sys.argv[1])+'/'+os.path.normpath(bench)
        files = []

        for (dirpath, dirnames, filenames) in walk(benchpath):
            for file in filenames:
                if file.endswith(".benchout"):
                    files.append(file)
            break 
        
        if len(files)==0:
            print("No files")
            break

        exectimes = []
        duration_re = re.compile(r"Total Duration: (\d+\.\d+) seconds")
        for file in files:
            
            with open(benchpath+"/"+file, "r") as lines:
                for line in lines:
                    # Match and extract the total duration
                    dur_match = duration_re.match(line)
                    if dur_match:
                        total_duration = dur_match.group(1)
                        total_duration = float(total_duration)  # Convert to nanoseconds
                        exectimes.append(total_duration)
                    
            
        exectimes.sort()
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

if __name__ == "__main__":
    main()

    
    
    



