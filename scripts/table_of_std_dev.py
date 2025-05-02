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
            case "0-6-":
                fin_name="RoamHKx2"
                
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
    parser.add_argument("--output", help="Path to the output file.", default=None)
    args = parser.parse_args()

    stats_files_c = find_stats_files(args.root_dirs)
    if not stats_files_c:
        print("No _stats.txt files found in the provided comparison directories.")
        return

    dict_c = populate_stats_dict(stats_files_c, args.root_dirs)

    #out_name = "-"
    #out_std_dev = "Standard deviation"
    #out_avg = "Average exec"
#
#
#
    #sorted_list = sorted(dict_c.items(), key = lambda y: tuple(reversed(y[0].split("-"))))
#
    #for name, stats in sorted_list:
    #    out_name = out_name + " & " + name
    #    out_std_dev = out_std_dev + " & " + str(round(dict_c[name]["Execution Times (seconds)"]["Standard Deviation"], 6))
    #    out_avg = out_avg + " & " + str(round(dict_c[name]["Execution Times (seconds)"]["Average"], 6))
    #    
    #out_name = out_name + r"\\  \hline"
    #out_std_dev = out_std_dev + r"\\  \hline"
    #out_avg = out_avg + r"\\  \hline"
#
    #out_prefix = r"\begin{tabularx}{1\textwidth} { "
    #for i in range(len(sorted_list)+1):
    #    out_prefix = "\n" + out_prefix + r"| >{\centering\arraybackslash}X "
    #out_prefix =  out_prefix + r"| }" +"\n"+ r'\hline'
#
    #print(out_prefix)
    #print(out_name)
    #print(out_avg)
    #print(out_std_dev)
    #print(r"\end{tabularx}")

    out_name_omp = r"\rowcolor{gray!40} OpenMP"
    out_std_dev_omp = r"Standard deviation"
    out_avg_omp = r"Average time"

    out_name_sycl = r"\rowcolor{gray!40} SYCL"
    out_std_dev_sycl = r"Standard deviation"
    out_avg_sycl = r"Average time"


    sorted_list = sorted(dict_c.items(), key = lambda y: tuple(reversed(y[0].split("-"))))

    for name, stats in sorted_list:
        if name.split("-")[-1] == "omp":
            out_name_omp = out_name_omp + " & " + name.split("-")[0]
            out_std_dev_omp = out_std_dev_omp + " & " + str(round(dict_c[name]["Execution Times (seconds)"]["Standard Deviation"], 6))
            out_avg_omp = out_avg_omp + " & " + str(round(dict_c[name]["Execution Times (seconds)"]["Average"], 6))
        else:
            out_name_sycl = out_name_sycl + " & " + name.split("-")[0]
            out_std_dev_sycl = out_std_dev_sycl + " & " + str(round(dict_c[name]["Execution Times (seconds)"]["Standard Deviation"], 6))
            out_avg_sycl = out_avg_sycl + " & " + str(round(dict_c[name]["Execution Times (seconds)"]["Average"], 6))


    out_name_omp = out_name_omp + r"\\  \hline"
    out_avg_omp = out_avg_omp + r"\\  \hline"
    out_std_dev_omp = out_std_dev_omp + r"\\  \hline"

    out_name_sycl = out_name_sycl + r"\\  \hline"
    out_avg_sycl = out_avg_sycl + r"\\  \hline"
    out_std_dev_sycl = out_std_dev_sycl + r"\\  \hline"


    out_prefix = r"\begin{tabularx}{1\textwidth} { "
    for i in range(len(sorted_list)//2+1):
        out_prefix = "\n" + out_prefix + r"| >{\centering\arraybackslash}X "
    out_prefix =  out_prefix + r"| }" +"\n"+ r'\hline'

    print(out_prefix)
    print(out_name_omp)
    print(out_avg_omp)
    print(out_std_dev_omp)
    print(out_name_sycl)
    print(out_avg_sycl)
    print(out_std_dev_sycl)
    print(r"\end{tabularx}")
    

    #comparison = compare_stats(all_stats, all_names, baseline_index)
    #print_comparison_html(comparison, all_names, baseline_index, args.output)

if __name__ == "__main__":
    main()
