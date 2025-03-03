import os
import re
import sys
import matplotlib.pyplot as plt

# Usage: Arg 1 contains the path to the folder where benchmark output folders are stored
# Arg 2 (optional) contains the path to the folder where graphs will be saved
def main():
    if len(sys.argv) < 2 or not os.path.exists(sys.argv[1]):
        print('First argument must be a valid path to the folder containing benchmark outputs.')
        return
    
    input_folder = sys.argv[1]
    output_folder = sys.argv[2] if len(sys.argv) > 2 else input_folder  # Use input folder as default for output

    if not os.path.exists(output_folder):
        print(f'Output folder does not exist: {output_folder}')
        return
    
    benches = os.listdir(input_folder)
    print(benches)

    for bench in benches:
        if not ("sycl" in bench or "omp" in bench):
            continue

        benchpath = os.path.join(input_folder, bench)
        if not os.path.isdir(benchpath):
            continue
        
        files = [f for f in os.listdir(benchpath) if f.endswith(".benchout")]
        
        if not files:
            print(f"No .benchout files found in {benchpath}")
            continue

        exectimes = []
        duration_re = re.compile(r"Total Duration: (\d+\.\d+) seconds")

        for file in files:
            file_path = os.path.join(benchpath, file)
            with open(file_path, "r") as lines:
                for line in lines:
                    dur_match = duration_re.match(line)
                    if dur_match:
                        total_duration = float(dur_match.group(1))
                        exectimes.append(total_duration)

        exectimes.sort()
        avgexectime = sum(exectimes) / len(exectimes)
        normexectimes = [x / avgexectime for x in exectimes]

        # Plot normalized execution times
        fig, axs = plt.subplots()
        axs.set_ylabel('Execution time (normalized)')
        axs.set_xlabel(bench)
        axs.boxplot([normexectimes])
        plt.xticks([])
        plt.savefig(os.path.join(output_folder, f"{bench}.png"))

        # Plot execution times in seconds
        fig, axs = plt.subplots()

        axs.set_ylabel('Execution time (s)')
        axs.set_xlabel(bench)
        axs.boxplot([exectimes])
        plt.xticks([])
        plt.savefig(os.path.join(output_folder, f"{bench}-sec.png"))

if __name__ == "__main__":
    main()
