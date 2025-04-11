import os
import re
import sys
import argparse
import matplotlib.pyplot as plt


def parse_arguments():
    parser = argparse.ArgumentParser(description="Generate combined execution time graphs from benchmark outputs.")
    parser.add_argument("input_folder", type=str, help="Path to the folder containing benchmark outputs.")
    parser.add_argument("-o","--output_folder", type=str, help="Path to the folder where the output graph will be saved.")
    parser.add_argument("-hl", "--horizontal-line", type=float, help="Optional horizontal line at given y-value")

    return parser.parse_args()
def main():
    parser = parse_arguments()
    if not os.path.exists(parser.input_folder):
        print('First argument must be a valid path to the folder containing benchmark outputs.')
        return    
    input_folder = parser.input_folder
    output_folder = parser.output_folder if parser.output_folder else input_folder  # Use input folder as default for output

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
    keys = exec_dict.keys()
    values = exec_dict.values()
    s = sorted(zip(keys, values), key = lambda y: tuple(reversed(y[0].split("-"))))

    # Change "-NSMT-" to something else if needed
    keys = [i[0].replace("-NSMT-", "-") for i in s]
    values = [i[1] for i in s]

    ax.set_title(os.path.basename(input_folder))
    ax.boxplot(values)
    ax.set_xticklabels(keys, fontsize=10)
    ax.grid(True, which="major", axis="x", linewidth=0.5, linestyle='--')
    ax.grid(True, which="major", axis="y", linewidth=0.5, linestyle='-')
    fig.autofmt_xdate()   
    fig.tight_layout(pad=2)

    if parser.horizontal_line:
        ax.axhline(y=parser.horizontal_line, color='r', linestyle='--', label=f"Horizontal line at {parser.horizontal_line}")

    for i, (tick, orig_label) in enumerate(zip(ax.xaxis.get_major_ticks(), keys)):
        
        # Replace "-SMT-" with any other string to change the color
        if "-SMT-" in orig_label:
            color = 'royalblue'
                        # Tick label and mark color
            tick.label1.set_color(color)
            tick.tick1line.set_color(color)
            tick.tick2line.set_color(color)
            tick.gridline.set_color(color)



    plt.savefig(os.path.join(output_folder, f"combined_boxplot.png"), dpi=250)

if __name__ == "__main__":
    main()