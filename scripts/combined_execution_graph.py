import os
import re
import sys
import matplotlib.pyplot as plt

def main():
    if len(sys.argv) < 2 or not os.path.exists(sys.argv[1]):
        print('First argument must be a valid path to the folder containing benchmark outputs.')
        return
    
    input_folder = sys.argv[1]
    output_folder = sys.argv[2] if len(sys.argv) > 2 else input_folder  # Use input folder as default for output

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    

    #r = re.compile(".*benchout")
    exec_dict = dict()

    for root, subdirs, files in os.walk(input_folder):
        print(root)
        benches = os.listdir(root)




        for bench in benches:
            if not ("sycl" in bench or "omp" in bench):
                continue

            benchpath = os.path.join(root, bench)
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
            bench.split("-")
            exec_dict[os.path.basename(root)+"-"+bench.split("-")[1]] = exectimes


    #plt.title(os.path.basename(input_folder))
    fig, ax = plt.subplots()
    #plt.grid(axis = 'y', linestyle = '--')

    ax.set_title(os.path.basename(input_folder))
    ax.boxplot(exec_dict.values())
    ax.set_xticklabels(exec_dict.keys(), fontsize=10)
    fig.autofmt_xdate()   
    
    plt.savefig(os.path.join(output_folder, f"combined_boxplot.png"), dpi=250)

if __name__ == "__main__":
    main()