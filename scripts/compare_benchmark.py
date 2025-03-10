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

def compare_stats(all_stats, all_names, baseline_index):
    comparison = {}
    sections = list(all_stats[0].keys())

    for section in sections:
        comparison[section] = {}
        for key in all_stats[0][section]:
            comparison[section][key] = {}
            for i, stats in enumerate(all_stats):
                comparison[section][key][all_names[i]] = stats[section][key]

            baseline_value = all_stats[baseline_index][section][key]
            for i, stats in enumerate(all_stats):
                if i == baseline_index:
                    comparison[section][key][f"{all_names[i]}_diff"] = 0
                    comparison[section][key][f"{all_names[i]}_pct_change"] = 0
                else:
                    current_value = stats[section][key]
                    diff = current_value - baseline_value
                    pct_change = ((current_value - baseline_value) / baseline_value) * 100 if baseline_value != 0 else 0
                    comparison[section][key][f"{all_names[i]}_diff"] = diff
                    comparison[section][key][f"{all_names[i]}_pct_change"] = pct_change
    return comparison

def get_color(value):
    """Helper function to return a color based on the percentage change."""
    if abs(value) > 10:
        return "#e57373"  # Light red
    elif abs(value) > 5:
        return "#ffeb3b"  # Light yellow
    else:
        return "#81c784"  # Light green

def print_comparison_html(comparison, all_names, baseline_index, output_file=None):
    short_names = []
    run_counter = 1
    absolute_paths = []  # Store the absolute paths of each run
    benchmark_folders = []  # Store the benchmark folder names
    for name in all_names:
        short_names.append(f"Run {run_counter}")
        absolute_paths.append(os.path.abspath(name))  # Save the absolute path
        run_counter += 1

    # Highlight the baseline run
    short_names[baseline_index] = f"<strong style='color:#81c784;'>{short_names[baseline_index]}</strong>"

    # Prepare the HTML output with Dark Mode theme
    output = f"""
    <html>
    <head>
        <style>
            body {{
                background-color: #121212;
                color: #E0E0E0;
                font-family: Arial, sans-serif;
                padding: 20px;
            }}
            h2, h3 {{
                color: #FFEB3B;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            th, td {{
                padding: 10px;
                border: 1px solid #333;
                text-align: center;
            }}
            th {{
                background-color: #333;
                color: #FFEB3B;
            }}
            tr:nth-child(even) {{
                background-color: #333;
            }}
            tr:nth-child(odd) {{
                background-color: #222;
            }}
            td {{
                color: #E0E0E0;
            }}
            .color-diff {{
                font-weight: bold;
            }}
            .color-red {{
                color: #e57373;
            }}
            .color-yellow {{
                color: #ffeb3b;
            }}
            .color-green {{
                color: #81c784;
            }}
        </style>
    </head>
    <body>
        <h2>Comparison Results</h2>
        <p>Legend (Baseline is {short_names[baseline_index]}):</p>
        <ul>
    """

    for i in range(len(all_names)):
        output += f"<li>{short_names[i]}: {absolute_paths[i]}</li>"
    
    output += "</ul>"

    for section, data in comparison.items():
        output += f"<h3>=== {section} ===</h3>\n"
        table = "<table>"
        
        # Headers: Metric, Run 1, Run 1 (vs baseline), Run 1 % Change, ...
        headers = ["Metric"] + short_names
        for i, name in enumerate(short_names):
            if i == baseline_index:
                continue
            else:
                headers.append(f"{name} (vs Baseline)")
                headers.append(f"{name} (% Change)")

        table += "<tr>"
        for header in headers:
            table += f"<th>{header}</th>"
        table += "</tr>"

        for key, values in data.items():
            row = f"<tr><td>{key}</td>"
            for name in all_names:
                row += f"<td>{values[name]:.6f}</td>"
            for i in range(len(all_names)):
                if i != baseline_index:
                    row += f"<td>{values[f'{all_names[i]}_diff']:.6f}</td>"
                    pct_change = values[f'{all_names[i]}_pct_change']
                    color_class = ""
                    if pct_change > 10:
                        color_class = "color-red"
                    elif pct_change > 5:
                        color_class = "color-yellow"
                    else:
                        color_class = "color-green"
                    row += f"<td class='{color_class}'>{pct_change:.2f}%</td>"
            row += "</tr>"
            table += row

        table += "</table>"
        output += table

    # Finalize the HTML output
    output += "</body></html>"

    # Set default output file if not provided
    if output_file is None:
        output_file = "comparison_output.html"

    # Write HTML to the file
    with open(output_file, 'w') as f:
        f.write(output)

    print(f"Comparison results saved to: {output_file}")



def main():
    parser = argparse.ArgumentParser(description="Compare benchmark results.")
    parser.add_argument("root_dirs", nargs="+", help="Root directories containing benchmark results.")
    parser.add_argument("--baseline", help="Absolute path to the baseline stats file.")
    parser.add_argument("--output", help="Path to the output HTML file.", default=None)
    args = parser.parse_args()

    stats_files = find_stats_files(args.root_dirs)
    if not stats_files:
        print("No _stats.txt files found in the provided directories.")
        return

    all_stats = []
    all_names = []

    # Load benchmark stats from root directories
    for stats_file in stats_files:
        name = os.path.relpath(stats_file, start=os.path.commonpath(args.root_dirs))
        all_names.append(name)
        stats = parse_stats_file(stats_file)
        all_stats.append(stats)

    # Handle baseline file if provided as an absolute path
    baseline_index = 0
    if args.baseline:
        baseline_path = os.path.abspath(args.baseline)
        if not os.path.isfile(baseline_path):
            print(f"Baseline file {baseline_path} not found.")
            return
        
        baseline_stats = parse_stats_file(baseline_path)
        all_names.insert(0, baseline_path)  # Add baseline as the first entry
        all_stats.insert(0, baseline_stats)  # Add baseline stats to the front
        baseline_index = 0  # Ensure baseline is the first entry
    
    comparison = compare_stats(all_stats, all_names, baseline_index)
    print_comparison_html(comparison, all_names, baseline_index, args.output)

if __name__ == "__main__":
    main()
