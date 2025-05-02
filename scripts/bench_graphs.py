import os
import re
import sys
import matplotlib.pyplot as plt
import numpy as np

def calculate_percentiles(data):
    return {
        'min': np.min(data),
        'max': np.max(data),
        '1th': np.percentile(data, 1),
        '10th': np.percentile(data, 10),
        '25th': np.percentile(data, 25),
        '50th': np.percentile(data, 50),
        '75th': np.percentile(data, 75),
        '90th': np.percentile(data, 90),
        '99th': np.percentile(data, 99),
    }

def write_statistics_to_file(output_folder, bench, exectimes, normexectimes):
    stats_file_path = os.path.join(output_folder, f"{bench}_stats.txt")
    percentiles = calculate_percentiles(exectimes)
    norm_percentiles = calculate_percentiles(normexectimes)
    
    with open(stats_file_path, "w") as stats_file:
        stats_file.write(f"Statistics for {bench}:\n")
        stats_file.write("\n--- Execution Times (seconds) ---\n")
        stats_file.write(f"Min: {percentiles['min']:.9f}\n")
        stats_file.write(f"1th percentile: {percentiles['1th']:.9f}\n")
        stats_file.write(f"10th percentile: {percentiles['10th']:.9f}\n")
        stats_file.write(f"25th percentile: {percentiles['25th']:.9f}\n")
        stats_file.write(f"50th percentile: {percentiles['50th']:.9f}\n")
        stats_file.write(f"75th percentile: {percentiles['75th']:.9f}\n")
        stats_file.write(f"90th percentile: {percentiles['90th']:.9f}\n")
        stats_file.write(f"99th percentile: {percentiles['99th']:.9f}\n")
        stats_file.write(f"Max: {percentiles['max']:.9f}\n")
        stats_file.write(f"Average: {np.mean(exectimes):.9f}\n")
        stats_file.write(f"Standard Deviation: {np.std(exectimes):.9f}\n")

        stats_file.write("\n--- Normalized Execution Times ---\n")
        stats_file.write(f"Min: {norm_percentiles['min']:.9f}\n")
        stats_file.write(f"1th percentile: {norm_percentiles['1th']:.9f}\n")
        stats_file.write(f"10th percentile: {norm_percentiles['10th']:.9f}\n")
        stats_file.write(f"25th percentile: {norm_percentiles['25th']:.9f}\n")
        stats_file.write(f"50th percentile: {norm_percentiles['50th']:.9f}\n")
        stats_file.write(f"75th percentile: {norm_percentiles['75th']:.9f}\n")
        stats_file.write(f"90th percentile: {norm_percentiles['90th']:.9f}\n")
        stats_file.write(f"99th percentile: {norm_percentiles['99th']:.9f}\n")
        stats_file.write(f"Max: {norm_percentiles['max']:.9f}\n")
        stats_file.write(f"Standard Deviation: {np.std(normexectimes):.9f}\n")

def main():
    if len(sys.argv) < 2 or not os.path.exists(sys.argv[1]):
        print('First argument must be a valid path to the folder containing benchmark outputs.')
        return
    
    input_folder = sys.argv[1]
    output_folder = sys.argv[2] if len(sys.argv) > 2 else input_folder  # Use input folder as default for output

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
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

        ## Plot normalized execution times
        #fig, axs = plt.subplots()
        #axs.set_ylabel('Execution time (normalized)')
        #axs.set_xlabel(bench)
        #axs.boxplot([normexectimes])
        #plt.xticks([])
        #plt.savefig(os.path.join(output_folder, f"{bench}.png"))

        # Plot execution times in seconds
        fig = plt.figure(figsize=(2, 3))
        ax = plt.subplot()
        ax.set_ylabel('Execution time (s)')
        ax.set_xlabel(bench)
        ax.boxplot([exectimes], False, vert=True, whis=0.75, positions=[0], widths=[0.5])
        plt.xticks([])
        plt.tight_layout() 
        plt.savefig(os.path.join(output_folder, f"{bench}-sec.png"))
        #plt.show()

        # Write statistics to file
        write_statistics_to_file(output_folder, bench, exectimes, normexectimes)

if __name__ == "__main__":
    main()