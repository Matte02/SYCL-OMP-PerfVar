import os
import sys
import re
import argparse
from multiprocessing import Pool
import json

# Constants
DEFAULT_WORKLOAD_NAME = "main"
DEFAULT_OUTPUT_FILENAME = "noise_config.json"
DEFAULT_MERGE_THRESHOLD = 0

def parse_arguments():
    """
    Parse and handle command-line arguments using argparse.

    Returns:
        Namespace: Parsed arguments as an object.
    """
    parser = argparse.ArgumentParser(
        description="Process trace files and compute noise configurations."
    )

    # Positional argument for the trace folder path
    parser.add_argument(
        "trace_folder_path", 
        type=str,
        help="Path to the folder containing trace files."
    )

    # Optional argument for workload name (defaults to 'main')
    parser.add_argument(
        "-w", "--workload_name", 
        type=str, 
        default=DEFAULT_WORKLOAD_NAME, 
        help="Name of the workload task (default: 'main')."
    )

    # Optional argument for output filename (defaults to 'noise_config.json')
    parser.add_argument(
        "-o", "--output_filename", 
        type=str, 
        default=DEFAULT_OUTPUT_FILENAME, 
        help="Output filename for storing noise configuration (default: 'noise_config.json')."
    )

    # Optional argument for the merge threshold (defaults to 0)
    parser.add_argument(
        "-m", "--merge_threshold", 
        type=int, 
        default=DEFAULT_MERGE_THRESHOLD, 
        help="Time gap in nanoseconds to consider two consecutive noise events as the same (default: 0)."
    )

    return parser.parse_args()

def main():
    # Parse command-line arguments
    args = parse_arguments()

    # Path to trace files
    trace_path = os.path.normpath(args.trace_folder_path)

    # Gather all raw trace files in the specified directory
    raw_trace_files = [file for file in os.listdir(trace_path) if file.endswith(".trace")]
    raw_trace_files.sort(key=lambda file: int(file.split("-")[2]))  # Sort by trace number

    # Create a multiprocessing pool to process traces in parallel
    pool = Pool()

    # Process all trace files into a list of trace data
    trace_list = pool.starmap(get_cpu_dict, [(file, trace_path) for file in raw_trace_files])

    print(f"Number of traces: {len(trace_list)}")

    # Find the worst trace (one with the maximum duration)
    worst_trace = max(trace_list, key=lambda x: x[1])
    print(f"Worst trace duration: {worst_trace[1]}")

    # Compute average trace to filter out inherent noise
    average_dict = compute_average_trace(trace_list)
    
    # Clean the worst trace by removing average noise
    clean_worst_trace(worst_trace[0], average_dict)

    # Separate the workload execution from the noise traces
    noise_dict, workload_exec = seperate_traces(worst_trace[0], args.workload_name)
    workload_exec.sort(key=lambda tup: tup[0])  # Sort by start time
    
    # Synchronize the start time of the workload with the noise traces
    sync_start_diff = workload_exec[0][0]

    # Merge consecutive noise events into one continuous event using the provided merge threshold
    combine_consecutive_noises(noise_dict, sync_start_diff, merge_threshold=args.merge_threshold)

    # Write the processed noise data to the specified output JSON file
    json_string = json.dumps(noise_dict, indent=4) 
    with open(args.output_filename, "w") as f:
        f.write(json_string)

def combine_consecutive_noises(noise_dict, sync_start_diff, merge_threshold=0):
    """
    Merges consecutive or closely spaced noise occurrences into single continuous events.

    Args:
        noise_dict (dict): Dictionary mapping CPU IDs to lists of noise events (start time, duration).
        sync_start_diff (int): Time offset to synchronize workload start to time 0.
        merge_threshold (int): Time gap (in nanoseconds) within which two noises are considered close enough to merge.

    Returns:
        dict: Updated noise_dict with merged noise events.
    """
    for cpu, noises in noise_dict.items():
        combined_noises = []
        next_start = -1
        next_duration = -1

        for noise in noises:
            adjusted_start = noise[0] - sync_start_diff  # Adjust noise start time
            duration = noise[1]

            # Skip noise events starting before the synchronized start
            if adjusted_start < 0: 
                continue

            # If no previous noise to combine, start a new combined event
            if next_start == -1:
                next_start = adjusted_start
                next_duration = duration
            else:
                # If the current noise is close to the previous one, combine them
                if next_start + next_duration + merge_threshold >= adjusted_start:
                    next_duration += duration + max(adjusted_start - (next_start + next_duration), 0)
                else:
                    # No overlap, add the previous noise event and reset
                    combined_noises.append((next_start, next_duration))
                    next_start = adjusted_start
                    next_duration = duration

        # Add the last combined noise event
        combined_noises.append((next_start, next_duration))
        noise_dict[cpu] = combined_noises

    return noise_dict


# Separates workload execution traces from noise traces.
def seperate_traces(cpu_dict, workload_task_name):
    """
    Separates workload execution traces from noise traces.

    Args:
        cpu_dict (dict): Dictionary of CPU traces with tasks and timings.
        workload_task_name (str): The name of the task representing the workload.

    Returns:
        tuple: A tuple containing:
            - noise_dict (dict): A dictionary of noise traces for each CPU.
            - workload_exec (list): A list of workload execution timings.
    """
    noise_dict = dict()
    workload_exec = []

    for cpu, tasks in cpu_dict.items():
        noise = []

        for task, timing_list in tasks.items():
            if task == workload_task_name:
                workload_exec.extend(timing_list) # Collect workload execution timings
            else:
                noise.extend(timing_list) # Collect noise timings

        # Sort noise timings for this CPU
        noise_dict[cpu] = sorted(noise, key=lambda tup: tup[0])

    return noise_dict, workload_exec

def clean_worst_trace(worst_trace, average_dict):
    """
    Removes the inherent average noise from the worst trace.

    Args:
        worst_trace (dict): The trace data for the worst trace (with CPU task timings).
        average_dict (dict): The average trace data to filter out from the worst trace.
    """
    for cpu, tasks in worst_trace.items():
        for task, timing_list in tasks.items():
            for timing, duration in average_dict[cpu][task]:
                if len(worst_trace[cpu][task]) <= 0:     # Skip if no data available
                    break

                # Find the closest matching duration in worst-case trace
                closest_idx = min(
                    range(len(worst_trace[cpu][task])), 
                    key=lambda i: abs(worst_trace[cpu][task][i][1] - duration)
                )

                # Adjust or remove the closest matching entry
                closest_timing, closest_duration = worst_trace[cpu][task][closest_idx]
                if closest_duration - duration < 0:
                    worst_trace[cpu][task] = (
                        worst_trace[cpu][task][:closest_idx] + 
                        worst_trace[cpu][task][closest_idx + 1:]
                    )
                else:
                    worst_trace[cpu][task][closest_idx] = (closest_timing, closest_duration - duration)

def compute_average_trace(trace_list):
    """
    Computes the average trace from a list of traces.

    Args:
        trace_list (list): A list of trace data tuples containing CPU task timings.

    Returns:
        dict: A dictionary containing the average timings for each CPU and task.
    """

    # Create average trace
    average_dict: dict[int, dict[str, list[(int, int)]]]
    average_dict = dict()
    # Gather all tasks
    for trace in trace_list:
        for cpu, tasks in trace[0].items():
            for task, timings in tasks.items():
                average_dict.setdefault(cpu, {}).setdefault(task, []).extend(timings)

    # Calculate the average duration for each task and CPU
    for cpu, tasks in average_dict.items():
        for task, timing_list in tasks.items():
            total_duration = 0  # Sum of all durations for averaging
            sampled_occurrences = []  # List to store sampled occurrences
            
            # Iterate over task timings and durations
            for i, (timing, duration) in enumerate(timing_list):
                total_duration += duration
                # Sample occurrences at intervals based on trace_list length
                if i % len(trace_list) == 0:
                    sampled_occurrences.append((timing, duration))
            
            # Compute average duration for the task
            average_duration = int(total_duration / len(timing_list))
            
            # Replace original task data with sampled occurrences and average duration
            average_dict[cpu][task] = [(timing, average_duration) for timing, _ in sampled_occurrences]
    return average_dict

def get_cpu_dict(file, trace_path):
    """
    Parses a trace file and extracts relevant information for CPU traces.

    Args:
        file (str): The trace file name.
        trace_path (str): The path to the directory containing the trace files.

    Returns:
        tuple: A tuple containing a dictionary of CPU traces and the total duration.
    """
    
    # Define regular expressions for matching the total duration and the second start time
    duration_re = re.compile(r"Total Duration: (\d+\.\d+) seconds")

    # Define Regex for matching traces
    trace_regex = re.compile(
        r"\[(\d{3})\]"                      # Capture CPU ID (three digits inside square brackets)
        r".*?noise:\s*"                     # Lazily match everything up to 'noise:'
        r"([^:]*[\/\w\-:]*|)"               # Capture the task name
        r"\s+start\s+"                      # Match 'start' keyword with spaces
        r"(\d+\.\d+)"                       # Capture the start time (floating-point number)
        r"\s+duration\s+"                   # Match 'duration' keyword with spaces
        r"(\d+)\s+ns"                       # Capture the duration (integer followed by 'ns')
    )

    # Initialize variables to store the extracted values from benchout
    total_duration = -1

    if file.endswith(".trace"):
        # Read total duration from .benchout file
        with open(os.path.join(trace_path, file.replace(".trace", ".benchout")), "r") as lines:
            for line in lines:
                if (match := duration_re.match(line)):
                    total_duration = int(match.group(1).replace(".", ""))
    
    
        #Dict(CPU,Dict(task,[(start,duration)]))
        cpu_dict: dict[int, dict[str, list[(int, int)]]]#= dict({'NULL': dict({'NULL': []})})
        cpu_dict = dict()
        # Parse trace file
        with open(os.path.join(trace_path, file), "r") as lines:
            for line in lines:
                if (match := trace_regex.search(line)):
                    cpu_id = int(match[1])                      # CPU ID
                    task = match[2].rsplit(":",1)[0] or "nmi"   # Task name
                    start = int(float(match[3]) * 1e9)          # Start Time (ns)
                    duration = int(match[4])                    # Duration (ns)

                    cpu_dict.setdefault(cpu_id, {}).setdefault(task, []).append((start, duration))

        #Sort all tasks based on start time (again)
        for tasks in cpu_dict.values():
            for task, timings in tasks.items():
                tasks[task] = sorted(timings, key=lambda x: x[0])

        return (cpu_dict, total_duration)

if __name__ == "__main__":
    main()

    
    
    



