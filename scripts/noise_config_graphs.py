import json
import matplotlib.pyplot as plt
import numpy as np
import argparse
import os

def load_noise_data(file_path):
    with open(file_path, "r") as f:
        return json.load(f)

def save_plot(plt, filename, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    plt.savefig(output_path)
    plt.close()

def plot_histograms(core_durations, all_durations, output_dir):
    sorted_cores = sorted(core_durations.keys(), key=int)
    num_cores = len(sorted_cores)
    cols = min(4, num_cores)
    rows = (num_cores + cols - 1) // cols
    
    fig, axes = plt.subplots(rows, cols, figsize=(4 * cols, 3 * rows))
    axes = axes.flatten() if num_cores > 1 else [axes]
    
    max_y = 0
    histograms = []
    
    for idx, core in enumerate(sorted_cores):
        durations = core_durations[core]
        hist, bins, _ = axes[idx].hist(durations, bins=np.logspace(np.log10(1e3), np.log10(max(durations, default=1e3)), 50), alpha=0.75, edgecolor='black')
        max_y = max(max_y, max(hist))
        histograms.append((axes[idx], hist, bins))
        axes[idx].set_xscale('log')
        axes[idx].set_xlabel("Noise Duration (ns)")
        axes[idx].set_ylabel("Frequency")
        axes[idx].set_title(f"Core {core}")
        axes[idx].grid(True)
    
    for ax, hist, bins in histograms:
        ax.set_ylim(0, max_y)
    
    for idx in range(num_cores, len(axes)):
        fig.delaxes(axes[idx])
    
    plt.tight_layout()
    save_plot(plt, "histograms_per_core.png", output_dir)
    
    plt.figure()
    plt.hist(all_durations, bins=np.logspace(np.log10(1e3), np.log10(max(all_durations, default=1e3)), 50), alpha=0.75, edgecolor='black')
    plt.xscale('log')
    plt.xlabel("Noise Duration (ns)")
    plt.ylabel("Frequency")
    plt.title("Noise Duration Distribution - All Cores")
    plt.grid(True)
    save_plot(plt, "histogram_all_cores.png", output_dir)

def plot_noise_counts(core_durations, output_dir):
    sorted_cores = sorted(core_durations.keys(), key=int)
    core_counts = {core: len(core_durations[core]) for core in sorted_cores}
    plt.figure()
    plt.bar(core_counts.keys(), core_counts.values(), color='blue', edgecolor='black')
    plt.xlabel("Core")
    plt.ylabel("Number of Noise Events")
    plt.title("Number of Noise Events per Core")
    plt.grid(axis='y')
    save_plot(plt, "noise_counts.png", output_dir)

def plot_noise_distribution_over_time(noise_data, output_dir):
    sorted_cores = sorted(noise_data.keys(), key=int)
    num_cores = len(sorted_cores)
    cols = min(4, num_cores)
    rows = (num_cores + cols - 1) // cols
    
    # Plot for each core
    fig, axes = plt.subplots(rows, cols, figsize=(4 * cols, 3 * rows))
    axes = axes.flatten() if num_cores > 1 else [axes]
    
    for idx, core in enumerate(sorted_cores):
        times = [event[0] for event in noise_data[core]]  # Assuming event[0] is the start time
        axes[idx].hist(times, bins='auto', alpha=0.75, edgecolor='black')
        axes[idx].set_xlabel("Start Time")
        axes[idx].set_ylabel("Frequency")
        axes[idx].set_title(f"Core {core} - Noise Distribution Over Time")
        axes[idx].grid(True)
    
    for idx in range(num_cores, len(axes)):
        fig.delaxes(axes[idx])
    
    plt.tight_layout()
    save_plot(plt, "noise_distribution_over_time_per_core.png", output_dir)
    
    # Combined plot for all cores
    all_times = [event[0] for core in noise_data for event in noise_data[core]]
    plt.figure()
    plt.hist(all_times, bins='auto', alpha=0.75, edgecolor='black')
    plt.xlabel("Start Time")
    plt.ylabel("Frequency")
    plt.title("Noise Distribution Over Time - All Cores")
    plt.grid(True)
    save_plot(plt, "noise_distribution_over_time_all_cores.png", output_dir)


def main():
    parser = argparse.ArgumentParser(description="Analyze noise data from a JSON file.")
    parser.add_argument("file_path", type=str, help="Path to the JSON file containing noise data.")
    parser.add_argument("output_directory", type=str, help="Path to benchmark directory.")
    args = parser.parse_args()

    base_output_dir = os.path.normpath(args.output_directory)
    print(f"Saving graphs to {base_output_dir}")
    noise_data = load_noise_data(args.file_path)
    core_durations = {core: [event[1] for event in events] for core, events in noise_data.items()}
    all_durations = [duration for durations in core_durations.values() for duration in durations]
    
    plot_histograms(core_durations, all_durations, base_output_dir)
    plot_noise_counts(core_durations, base_output_dir)
    plot_noise_distribution_over_time(noise_data, base_output_dir)

if __name__ == "__main__":
    main()