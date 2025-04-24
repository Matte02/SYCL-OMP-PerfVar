import os
import re
import argparse
from tabulate import tabulate
from termcolor import colored

def find_stats_files(root_dirs):
    stats_files = []
    for root_dir in root_dirs:
        for dirpath, _, filenames in os.walk(root_dir):
            for filename in filenames:
                if filename.endswith("_stats.txt"):
                    stats_files.append(os.path.join(dirpath, filename))
    return stats_files

def parse_stats_file(file_path):
    stats = {}
    with open(file_path, "r") as file:
        current_section = None
        for line in file:
            line = line.strip()
            if line.startswith("---"):
                current_section = line.strip("- ")
                stats[current_section] = {}
            elif line and current_section:
                key, value = line.split(":", 1)
                stats[current_section][key.strip()] = float(value.strip())
    return stats

def populate_stats_dict(stats_files, root_path):
    all_stats = []
    all_names = []
    stats_dict = dict()

    # Load benchmark stats from root directories
    for stats_file in stats_files:
        name = os.path.relpath(stats_file, start=os.path.commonpath(root_path))
        fin_name = name.split("/")[0]

        match fin_name[:4]:
            case "0-8-":
                fin_name="Roam"
            case "0-7-":
                fin_name="RoamHK"
            case "1-8-":
                fin_name="TP"
            case "2-8-":
                fin_name="TPHK"
            case "2-7-":
                fin_name="TPHKx2"
                
        if "sycl" in name:
            fin_name = fin_name+"-sycl"
        elif "omp" in name:
            fin_name = fin_name+"-omp"

        #all_names.append(fin_name)
        stats = parse_stats_file(stats_file)
        #all_stats.append(stats)
        stats_dict[fin_name] = stats

    return stats_dict


def main():
    parser = argparse.ArgumentParser(description="Compare benchmark results.")
    parser.add_argument("root_dirs", nargs="+", help="Root directories containing compared benchmark results.")
    parser.add_argument("baseline_dirs", nargs="+", help="Root directories containing baseline benchmark results.")
    parser.add_argument("--output", help="Path to the output file.", default=None)
    args = parser.parse_args()

    stats_files_c = find_stats_files(args.root_dirs)
    if not stats_files_c:
        print("No _stats.txt files found in the provided comparison directories.")
        return

    stats_files_b = find_stats_files(args.baseline_dirs)
    if not stats_files_c:
        print("No _stats.txt files found in the provided baseline directories.")
        return

    dict_c = populate_stats_dict(stats_files_c, args.root_dirs)
    dict_b = populate_stats_dict(stats_files_b, args.baseline_dirs)

    print(dict_c["Roam-omp"]["Execution Times (seconds)"]["Average"])

    out_name = "-"
    out_avg_change = "Change from baseline"
    out_avg_abs = "Average time"


    sorted_list = sorted(dict_c.items(), key = lambda y: tuple(reversed(y[0].split("-"))))

    for name, stats in sorted_list:
        out_name = out_name + " & " + name
        out_avg_abs = out_avg_abs + " & " + str(round(dict_c[name]["Execution Times (seconds)"]["Average"], 6))
        change = float(dict_c[name]["Execution Times (seconds)"]["Average"]) / float(dict_b[name]["Execution Times (seconds)"]["Average"]) - 1 
        
        out_avg_change = out_avg_change + " & " + str(round(change*100, 1)) + r"\%"

    out_name = out_name + r"\\  \hline"
    out_avg_abs = out_avg_abs + r"\\  \hline"
    out_avg_change = out_avg_change + r"\\  \hline"

    out_prefix = r"\begin{tabularx}{1\textwidth} { "
    for i in range(len(sorted_list)+1):
        out_prefix = "\n" + out_prefix + r"| >{\centering\arraybackslash}X "
    out_prefix =  out_prefix + r"| }" +"\n"+ r'\hline'

    print(out_prefix)
    print(out_name)
    print(out_avg_abs)
    print(out_avg_change)
    print(r"\end{tabularx}")
    #comparison = compare_stats(all_stats, all_names, baseline_index)
    #print_comparison_html(comparison, all_names, baseline_index, args.output)

if __name__ == "__main__":
    main()
