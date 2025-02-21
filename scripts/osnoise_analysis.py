import os
import sys
import re
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict

def parse_benchout(filepath):
    """
    Parses a .benchout file to extract the start and end times.
    Returns a tuple (start_time, end_time).
    """
    start_time_pattern = re.compile(r"Start time: ([\d.]+) seconds")
    end_time_pattern = re.compile(r"End time: ([\d.]+) seconds")

    start_time = None
    end_time = None

    with open(filepath, "r") as file:
        for line in file:
            start_match = start_time_pattern.search(line)
            end_match = end_time_pattern.search(line)
            if start_match:
                start_time = float(start_match.group(1))
            if end_match:
                end_time = float(end_match.group(1))

    if start_time is None or end_time is None:
        raise ValueError("Could not find start or end time in the benchout file.")

    return start_time, end_time

def parse_osnoise_trace(filepath, main_task_name, start_time, end_time):
    """
    Parses an osnoise trace file and extracts noise event information.
    Returns a dictionary {cpu: [(timestamp, duration)]} for noise events within the time range.
    """
    osnoise_pattern = re.compile(
        r".*\[(\d{3})\].*thread_noise:.*start (\d+\.\d+) duration (\d+) ns"
    )
    
    noise_data = defaultdict(list)
    
    with open(filepath, "r") as file:
        for line in file:
            match = osnoise_pattern.search(line)
            if match:
                cpu = int(match.group(1))
                timestamp = float(match.group(2))  # Time in seconds
                duration = int(match.group(3)) / 1000  # Convert ns to µs
                
                # Filter out main task noise events and only include within start and end times
                if main_task_name not in line and start_time <= timestamp <= end_time:
                    noise_data[cpu].append((timestamp, duration))

    return noise_data

def plot_noise_frequency(noise_data, bin_size=0.01):
    """
    Plots the frequency of noise events over time.
    """
    all_timestamps = [event[0] for events in noise_data.values() for event in events]
    if not all_timestamps:
        print("No noise events to analyze.")
        return

    min_time, max_time = min(all_timestamps), max(all_timestamps)
    bins = np.arange(min_time, max_time, bin_size)

    plt.figure(figsize=(10, 6))
    plt.hist(all_timestamps, bins=bins, edgecolor='black', alpha=0.7)
    plt.xlabel("Time (s)")
    plt.ylabel("Noise Event Count")
    plt.title(f"Noise Event Frequency (Bin Size: {bin_size}s)")
    plt.show()

def plot_noise_durations(noise_data):
    """
    Plots a histogram of noise event durations.
    """
    all_durations = [event[1] for events in noise_data.values() for event in events]
    
    if not all_durations:
        print("No noise events to analyze.")
        return

    plt.figure(figsize=(10, 6))
    plt.hist(all_durations, bins=50, edgecolor='black', alpha=0.7)
    plt.xlabel("Noise Duration (µs)")
    plt.ylabel("Frequency")
    plt.title("Distribution of Noise Event Durations")
    plt.xscale("log")  # Log scale to handle large variations
    plt.show()

def plot_heatmap(noise_data, time_bin_size=0.01):
    """
    Creates a heatmap of noise durations over time across CPUs.
    """
    if not noise_data:
        print("No noise events to analyze.")
        return

    min_time = min(event[0] for events in noise_data.values() for event in events)
    max_time = max(event[0] for events in noise_data.values() for event in events)
    bins = np.arange(min_time, max_time, time_bin_size)
    
    cpu_list = sorted(noise_data.keys())
    cpu_index = {cpu: idx for idx, cpu in enumerate(cpu_list)}
    
    heatmap_data = np.zeros((len(cpu_list), len(bins) - 1))

    for cpu, events in noise_data.items():
        timestamps, durations = zip(*events)
        hist, _ = np.histogram(timestamps, bins=bins, weights=durations)
        heatmap_data[cpu_index[cpu], :] = hist

    plt.figure(figsize=(12, 6))
    sns.heatmap(heatmap_data, cmap="Reds", xticklabels=50, yticklabels=cpu_list)
    plt.xlabel("Time (s)")
    plt.ylabel("CPU")
    plt.title("Heatmap of Noise Duration Across CPUs (Main Task Filtered)")
    plt.show()

def plot_interarrival_times(noise_data):
    """
    Plots the distribution of inter-arrival times between noise events.
    """
    interarrivals = []
    for events in noise_data.values():
        timestamps = [e[0] for e in events]
        if len(timestamps) > 1:
            diffs = np.diff(sorted(timestamps))
            interarrivals.extend(diffs)

    if not interarrivals:
        print("No interarrival times to analyze.")
        return

    plt.figure(figsize=(10, 6))
    plt.hist(interarrivals, bins=50, edgecolor='black', alpha=0.7)
    plt.xlabel("Interarrival Time (s)")
    plt.ylabel("Frequency")
    plt.title("Distribution of Noise Event Interarrival Times")
    plt.xscale("log")
    plt.show()

def noise_characterization(noise_data):
    """
    Analyzes and characterizes noise durations across all CPUs.
    """
    all_durations = [event[1] for events in noise_data.values() for event in events]
    
    if not all_durations:
        print("No noise events to analyze.")
        return

    mean_duration = np.mean(all_durations)
    median_duration = np.median(all_durations)
    std_duration = np.std(all_durations)
    percentiles = np.percentile(all_durations, [25, 50, 75, 90, 95])

    print("Noise Duration Statistics:")
    print(f"Mean: {mean_duration:.2f} µs")
    print(f"Median: {median_duration:.2f} µs")
    print(f"Standard Deviation: {std_duration:.2f} µs")
    print(f"Percentiles (25, 50, 75, 90, 95): {percentiles}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python plot_osnoise.py <osnoise_trace_file> <main_task_name>")
        return
    
    trace_filepath = sys.argv[1]
    main_task_name = sys.argv[2]

    benchout_filepath = trace_filepath.rsplit('.', 1)[0] + ".benchout"
    
    if not os.path.isfile(trace_filepath) or not os.path.isfile(benchout_filepath):
        print("Invalid file path.")
        return

    # Get start and end times from the benchout file
    start_time, end_time = parse_benchout(benchout_filepath)
    
    # Parse the osnoise trace file and filter by the start and end times
    noise_data = parse_osnoise_trace(trace_filepath, main_task_name, start_time, end_time)

    noise_characterization(noise_data)
    plot_noise_frequency(noise_data)
    plot_noise_durations(noise_data)
    plot_heatmap(noise_data)

if __name__ == "__main__":
    main()
