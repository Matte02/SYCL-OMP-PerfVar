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
DEFAULT_COMBINE_SMT = False


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

    # Optional argument for the merging of simultaneous multithreaded traces (defaults to 0)
    parser.add_argument(
        "-smt", "--combine_threads", 
        type=bool, 
        default=DEFAULT_COMBINE_SMT, 
        help="Sets if two consecutive threads from traces should be combined into one, thereby merging simultaneous multithreading (default: False)."
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

    print(f"Number of traces: {len(raw_trace_files)}")

    # Find the worst trace (one with the maximum duration)
    worst_trace = get_worst_case_dict(raw_trace_files, trace_path, args.workload_name, args.combine_threads)
    print(f"Worst trace duration: {worst_trace[1]}")

    # Compute average trace to filter out inherent noise
    average_dict = compute_average_trace(raw_trace_files, trace_path, args.workload_name, args.combine_threads)
    print(f"Average dict created")

    # Clean the worst trace by removing average noise
    clean_worst_trace(worst_trace, average_dict)
    print(f"Cleaned worst case")

    # Separate the workload execution from the noise traces
    noise_dict, _ = seperate_traces(worst_trace[0], args.workload_name)
    print(f"Seperated workload from trace")

    # Merge consecutive noise events into one continuous event using the provided merge threshold
    combine_consecutive_noises(noise_dict, merge_threshold=args.merge_threshold)
    print(f"Combined overlapping noise")

    # Write the processed noise data to the specified output JSON file
    json_string = json.dumps(noise_dict, indent=4) 
    with open(args.output_filename, "w") as f:
        f.write(json_string)

def combine_consecutive_noises(noise_dict, merge_threshold=0):
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
            start = noise[0]
            duration = noise[1]

            # If no previous noise to combine, start a new combined event
            if next_start == -1:
                next_start = start
                next_duration = duration
            else:
                # If the current noise is close to the previous one, combine them
                if next_start + next_duration + merge_threshold >= start:
                    next_duration += duration + max(start - (next_start + next_duration), 0)
                else:
                    # No overlap, add the previous noise event and reset
                    combined_noises.append((next_start, next_duration))
                    next_start = start
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

    swapper_re = re.compile(r"swapper")

    for cpu, tasks in cpu_dict.items():
        noise = []
        workload_cpu = []
        swapper_cpu = []
        for task, timing_list in tasks.items():
            match = swapper_re.search(task)
            if match != None: # Collect instances of the swapper task
                swapper_cpu.extend(timing_list)
                continue
            if task == workload_task_name:
                workload_exec.extend(timing_list) # Collect workload execution timings
            else:
                noise.extend(timing_list) # Collect noise timings

        # Filter swapper tasks related to the execution of the workload
        # This removes the context switch overhead stemming from workload
        assert len(swapper_cpu) >= len(workload_cpu)
        swapper_cpu = sorted(swapper_cpu, key=lambda tup: tup[0])
        # For each work instance remove the previous occurence of the swapper task 
        # as it should have been caused by the workload context swich
        for work_timing in workload_cpu: 
            prev_swap = 0
            for swap_timing in swapper_cpu:
                # Check if the next instance of swapper happened later than the
                # start of the workload instance
                if work_timing[0] - swap_timing[0] < 0:
                    # Swapper instance related to the workload instance has been found
                    break
                prev_swap = swap_timing
            swapper_cpu.remove(prev_swap)
        
        # Add unrelated swapper task instances to inherent noise list
        noise.extend(swapper_cpu)


        # Sort noise timings for this CPU
        noise_dict[cpu] = sorted(noise, key=lambda tup: tup[0])
        workload_exec.extend(workload_cpu)

    workload_exec.sort(key=lambda tup: tup[0])
    return noise_dict, workload_exec

def clean_worst_trace(worst_trace, average_dict):
    """
    Removes the inherent average noise from the worst trace.

    Args:
        worst_trace (dict, duration): The trace data for the worst trace (with CPU task timings).
        average_dict (dict): The average trace data to filter out from the worst trace.
    """
    # TODO: Parallelize loop
    for cpu, tasks in worst_trace[0].items():
        for task, _ in tasks.items():
            try:
                avg_frequency, avg_duration = average_dict[cpu][task]
            except:
                continue
            print(int(avg_frequency * worst_trace[1]))
            for x in range(int(avg_frequency * worst_trace[1])):
                if len(worst_trace[0][cpu][task]) <= 0:     # Skip if no data available
                    break
                # Find the closest matching duration in worst-case trace
                closest_idx = min(
                    range(len(worst_trace[0][cpu][task])), 
                    key=lambda i: abs(worst_trace[0][cpu][task][i][1] - avg_duration)
                )

                # Adjust or remove the closest matching entry
                closest_timing, closest_duration = worst_trace[0][cpu][task][closest_idx]
                if closest_duration - avg_duration < 0:
                    worst_trace[0][cpu][task] = (
                        worst_trace[0][cpu][task][:closest_idx] + 
                        worst_trace[0][cpu][task][closest_idx + 1:]
                    )
                else:
                    worst_trace[0][cpu][task][closest_idx] = (closest_timing, closest_duration - avg_duration)

#Used for multiprocessed map call
def get_frequency_duration_dict(file, trace_path, workload_name, combine_threads=False):
    """
    Produces a dictionary consisting of the frequency of a 
    task and the total duration on each present CPUs
        
    Args:
        file (str): The trace file name.
        trace_path (str): The path to the directory containing the trace files.
        workload_name (str): The name of the task representing the workload.

    Returns:
        dict: A dictionary containing the frequency and duration for each CPU and task.
    """
    trace  = get_cpu_dict(file, trace_path, workload_name)
    #f_d_dict: dict[int, dict[str, (int, int)]]
    f_d_dict = dict()
    for cpu, tasks in trace[0].items():
        for task, timings in tasks.items():
            for timing in timings:
                duration = timing[1]
                old_val = f_d_dict.setdefault(cpu, {}).setdefault(task, (0, 0))
                #Increment occurence amount and add to total duration of this task
                f_d_dict[cpu][task] = (old_val[0]+1, old_val[1]+duration)

            #Convert task occurences to frequency of task
            if cpu in f_d_dict:
                if task in f_d_dict[cpu]:
                    f_d_dict[cpu][task] = (f_d_dict[cpu][task][0] / trace[1], f_d_dict[cpu][task][1])

    return f_d_dict

def compute_average_trace(raw_trace_files, trace_path, workload_name, combine_threads=False):
    """
    Produces a dictionary consisting of the average frequency of a 
    task and the average duration on each present thread
        
    Args:
        raw_trace_files [str]: List of trace files to be evaluated.
        trace_path (str): The path to the directory containing the trace files.
        workload_name (str): The name of the task representing the workload.

    Returns:
        dict: A dictionary containing the average frequency and durations for each CPU and task.
    """

    #Get frequency and duration of tasks on all cpus on all traces
    pool = Pool()
    f_d_list = pool.starmap(get_frequency_duration_dict, [(file, trace_path, workload_name, combine_threads) for file in raw_trace_files])
    
    average_dict: dict[int, dict[str, (int, int)]]
    average_dict = dict()

    # Accumulate frequency and duration of all tasks in traces
    for f_d_dict in f_d_list:
        for cpu, tasks in f_d_dict.items():
            for task, (frequency, duration) in tasks.items():
                old_val = average_dict.setdefault(cpu, {}).setdefault(task, (0, 0))
                average_dict[cpu][task] = (old_val[0]+frequency, old_val[1]+duration)

    # Calculate the average frequency and duration for each task on each CPU
    for cpu, tasks in average_dict.items():
        for task, avg_tup in tasks.items():
            average_dict[cpu][task] = (float(average_dict[cpu][task][0]/len(raw_trace_files)), int(average_dict[cpu][task][1]//len(raw_trace_files)))
    return average_dict

def get_cpu_dict(file, trace_path, workload_name, combine_threads=False):
    """
    Parses a trace file and extracts relevant information for CPU traces.

    Args:
        file (str): The trace file name.
        trace_path (str): The path to the directory containing the trace files.
        workload_name (str): The name of the task representing the workload.

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
        workload_start_time = -1
        with open(os.path.join(trace_path, file), "r") as lines:
            for line in lines:
                if (match := trace_regex.search(line)):
                    cpu_id = int(match[1])                      # CPU ID
                    task = match[2].rsplit(":",1)[0] or "nmi"   # Task name
                    start = int(match[3].replace(".", ""))          # Start Time (ns)
                    duration = int(match[4])                    # Duration (ns)
                    if (task == workload_name and (workload_start_time == -1 or workload_start_time > start) ):
                        workload_start_time = start
                    #Store to cpu_dict and combine threads if this is enabled to remove SMT threads
                    if combine_threads:
                        cpu_dict.setdefault(cpu_id-(cpu_id%2), {}).setdefault(task, []).append((start, duration))
                    else:
                        cpu_dict.setdefault(cpu_id, {}).setdefault(task, []).append((start, duration))

        m_cpu_dict: dict[int, dict[str, list[(int, int)]]]#= dict({'NULL': dict({'NULL': []})})
        m_cpu_dict = dict()

        #Sort all tasks based on start time and remove unneccesary noise
        for cpu, tasks in cpu_dict.items():
            for task, timings in tasks.items():
                #Remove unneccessary noise before workload window and set time instant 0 to workload start time
                if workload_start_time >= 0:
                    adjusted_timings = list()
                    for timing in timings:
                        start = timing[0]
                        duration = timing[1]
                        # Noise started after workload and before end
                        if start >= workload_start_time and start<=workload_start_time+total_duration:
                            adjusted_timings.append((start-workload_start_time, duration))
                        # Noise started before workload but stretches past workload start
                        elif (start+duration) > workload_start_time and start<=workload_start_time+total_duration:
                            adjusted_timings.append((0, (start+duration)-workload_start_time))
                else:
                    print("No workload found in trace")
                    exit(1)
                m_cpu_dict.setdefault(cpu, {}).setdefault(task, [])
                m_cpu_dict[cpu][task] = sorted(adjusted_timings, key=lambda x: x[0])

        return (m_cpu_dict, total_duration)

#Used for multiprocessed map call
def get_file_duration_tuple(file, trace_path):
    """
    Fetches the durations of a workload execution for the provided trace

    Args:
        file (str): The trace file name.
        trace_path (str): The path to the directory containing the trace files.

    Returns:
        tuple: A tuple containing the trace file name and the associated workload duration.
    """
    # Define regular expressions for matching the total duration and the second start time
    duration_re = re.compile(r"Total Duration: (\d+\.\d+) seconds")
    with open(os.path.join(trace_path, file.replace(".trace", ".benchout")), "r") as lines:
                    for line in lines:
                        if (match := duration_re.match(line)):
                            total_duration = int(match.group(1).replace(".", ""))
                    return (file, total_duration)
    
def get_worst_case_dict(raw_trace_files, trace_path, workload_name, combine_threads=False):
    """
    Finds and fetches the dictionary of the trace with worst-case duration
    
    Args:
        raw_trace_files [str]: List of trace files to be evaluated.
        trace_path (str): The path to the directory containing the trace files.
        workload_name (str): The name of the task representing the workload.

    Returns:
        tuple: A tuple containing a dictionary of CPU traces and the total duration.
    """

    pool = Pool()
    duration_list = pool.starmap(get_file_duration_tuple, [(file, trace_path) for file in raw_trace_files])
        
    worst_case_file, _ = max(duration_list, key=lambda x: x[1])
    return (get_cpu_dict(worst_case_file, trace_path, workload_name, combine_threads))


if __name__ == "__main__":
    main()

    
    
    



