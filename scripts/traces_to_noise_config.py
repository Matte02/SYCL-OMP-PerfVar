import os
import sys
import re
import argparse
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm
import numpy as np
from multiprocessing import Pool
import json

# Constants
DEFAULT_WORKLOAD_NAME = "main"
DEFAULT_OUTPUT_FILENAME = "noise_config.json"
DEFAULT_MERGE_THRESHOLD = 0
DEFAULT_COMBINE_SMT = False
DEBUG = False

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
    worst_trace = clean_worst_trace(worst_trace, average_dict)
    print(f"Cleaned worst case")

    # Convert worst_trace dict to noise dict
    noise_dict = cpu_to_noise_dict(worst_trace[0],  worst_trace[1])
    print(f"Converted to Noise dict")

    if DEBUG == True:
        json_string = json.dumps(noise_dict, indent=4) 
        with open("Temp_Task_dict.json", "w") as f:
            f.write(json_string)

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
        max_prio = 99

        for (start, duration, priority) in noises:
            # If no previous noise to combine, start a new combined event
            if next_start == -1:
                next_start = start
                next_duration = duration
                max_prio = priority
            else:
                # If the current noise is close to the previous one, combine them
                if next_start + next_duration + merge_threshold >= start:
                    next_duration += duration + max(start - (next_start + next_duration), 0)
                    max_prio = priority if priority<max_prio else max_prio
                else:
                    # No overlap, add the previous noise event and reset
                    # Only include if above merge threshold in duration
                    if next_duration > merge_threshold:
                        combined_noises.append((next_start, next_duration, max_prio))

                    next_start = start
                    next_duration = duration
                    max_prio = priority


        # Add the last combined noise event
        combined_noises.append((next_start, next_duration, max_prio))
        noise_dict[cpu] = combined_noises

    return noise_dict


# Converts a cpu dict "dict(dict(list(tuple)))" to a noise dict dict(list(tuple)).
def cpu_to_noise_dict(cpu_dict, workload_end):
    """
    Converts a cpu dict "dict(dict(list(tuple)))" to a noise dict "dict(list(tuple))".

    Args:
        cpu_dict (dict): Dictionary of CPU traces with tasks and timings.
        workload_end (int): Time when workload is finished.

    Returns:
        noise_dict (dict): A dictionary of noise traces for each CPU.
    """
    noise_dict = dict()
    workload_exec = []

    for cpu, tasks in cpu_dict.items():
        noise = []
        for task, timing_list in tasks.items():
                noise.extend(timing_list) # Collect noise timings

        # Sort noise timings for this CPU
        noise_dict[cpu] = sorted(noise, key=lambda tup: tup[0])
        # Append end noise when workload finished. Used to sync looping during noise injection
        noise_dict[cpu].append((workload_end, 0, 0))

    workload_exec.sort(key=lambda tup: tup[0])
    return noise_dict

def clean_worst_trace(worst_trace, average_dict):
    """
    Removes the inherent average noise from the worst trace.

    Args:
        worst_trace (dict, duration): The trace data for the worst trace (with CPU task timings).
        average_dict (dict): The average trace data to filter out from the worst trace.
    """

    #cpu_amount = len(worst_trace[0])
    cpus = sorted(list(worst_trace[0].keys()))
    cpu_amount = len(cpus)

    # Calculate global average frequency and duration
    global_avg = {}
    for cpu, task_dict in average_dict.items():
        for task, (avg_frequency, avg_duration) in task_dict.items():
            temp_avg = global_avg.setdefault(task, (float(0), 0))
            global_avg[task] = (temp_avg[0] + avg_frequency, temp_avg[1] + avg_duration)

    for task, (sum_avg_freq, sum_avg_dur) in global_avg.items():
        global_avg[task] = (int(sum_avg_freq * worst_trace[1]), int(sum_avg_dur/cpu_amount))

    # Remove average noise from worst_trace
    for task, (occurences, avg_duration) in global_avg.items():
        # Create list of average noise removal order
        abs_timings = [() for x in range(cpus[len(cpus)-1]+1)]
        for cpu in cpus:
            if task in worst_trace[0][cpu]:
                abs_timings[cpu] = sorted(enumerate(worst_trace[0][cpu][task]), key=lambda x: abs(x[1][1]-avg_duration))

        rem_dur = 0
        # Remove (avg freq * worst case trace timeframe) instances from trace
        for x in range(occurences):
            global_closest_idx = -1
            global_closest_cpu = -1
            global_closest_abs = -1
            global_closest_local_idx = -1
            
            # Find closest matching noise globally
            for cpu in cpus:
                closest_idx = -1
                closest_abs = -1
                closest_local_idx = -1
                # Iterate over abs_timing until absolute difference increases, signaling closest entry has been reached
                for (local_idx, (idx, (_, dur, _))) in enumerate(abs_timings[cpu]):
                    if closest_idx == -1 or abs(dur - avg_duration) < closest_abs:
                        closest_abs = abs(dur - avg_duration)
                        closest_idx = idx
                        closest_local_idx = local_idx
                    else:
                        break
                
                # If found noise is closer then set it as global closest noise
                if closest_idx > -1 and (global_closest_cpu == -1 or (
                    global_closest_abs > closest_abs
                    )):
                    global_closest_idx = closest_idx
                    global_closest_cpu = cpu
                    global_closest_abs = closest_abs
                    global_closest_local_idx = closest_local_idx
            
            # Adjust or remove the closest matching entry
            if global_closest_cpu != -1:
                start, duration, priority = worst_trace[0][global_closest_cpu][task][global_closest_idx]
                if duration - avg_duration < 0:
                    worst_trace[0][global_closest_cpu][task][global_closest_idx] = (start, 0, priority)
                    abs_timings[global_closest_cpu] = (
                        abs_timings[global_closest_cpu][:global_closest_local_idx] + 
                        abs_timings[global_closest_cpu][global_closest_local_idx + 1:]
                    )
                    # Increase amount of excess duration accumualted
                    rem_dur += avg_duration - duration
                else:
                    worst_trace[0][global_closest_cpu][task][global_closest_idx] = (start, duration - avg_duration, priority)
                    abs_timings[global_closest_cpu][global_closest_local_idx] = (abs_timings[global_closest_cpu][global_closest_local_idx][0], (start, duration - avg_duration, priority))

        ## Remove smallest noises with the excess gathered when removing noises smaller than avg_duration
        #sorted_timings = [] #[(cpu, (idx, (start, dur)))]
        #for cpu in range(cpu_amount):
        #    sorted_timings.extend([(cpu, x) for x in abs_timings[cpu]])
#
        #sorted_timings = sorted(sorted_timings, key=lambda x: x[1][1][1])
        #i = 0
        ## Remove/ reduce smallest noises of this task with the acummulated excess duration
        #while rem_dur>0 and i<len(sorted_timings):
        #    cpu = sorted_timings[i][0]
        #    idx = sorted_timings[i][1][0]
        #    # Consume excess duration
        #    if worst_trace[0][cpu][task][idx][1] - rem_dur >= 0:
        #        worst_trace[0][cpu][task][idx] = (worst_trace[0][cpu][task][idx][0], worst_trace[0][cpu][task][idx][1] - rem_dur)
        #        rem_dur = 0
        #    else: #Reduce excess duration
        #        worst_trace[0][cpu][task][idx] = (worst_trace[0][cpu][task][idx][0], 0)
        #        rem_dur = rem_dur - worst_trace[0][cpu][task][idx][1]
        #    i+=1

        # Filter out noise with duration of 0
        for cpu in cpus:
            if task in worst_trace[0][cpu]:
                worst_trace[0][cpu][task] = [x for x in worst_trace[0][cpu][task] if x[1] != 0]

    if DEBUG == True:
        task_duration_dict = dict()
        for cpu, task_dict in worst_trace[0].items():
            for task, timings in task_dict.items():
                for timing in timings:
                    task_duration_dict[task][cpu] = task_duration_dict.setdefault(task, dict()).setdefault(cpu, 0) + timing[1]

        json_string = json.dumps(task_duration_dict, indent=4) 
        with open("temp_task_duration_dict.json", "w") as f:
            f.write(json_string)

        fig, ax = plt.subplots()    
        for cpu, task_dict in worst_trace[0].items():
            color = iter(cm.rainbow(np.linspace(0, 1, len(task_dict.keys()))))
            for task, timings in task_dict.items():
                c = next(color)
                for timing in timings:
                    ax.barh(cpu, width=timing[1], left=timing[0], color=c)
        plt.show()

    return worst_trace        

    # Old isolated processor place method
    ## TODO: Parallelize loop
    #for cpu, tasks in worst_trace[0].items():
    #    for task, _ in tasks.items():
    #        try:
    #            avg_frequency, avg_duration = average_dict[cpu][task]
    #        except:
    #            continue
    #        print(int(avg_frequency * worst_trace[1]))
    #        for x in range(int(avg_frequency * worst_trace[1])):
    #            if len(worst_trace[0][cpu][task]) <= 0:     # Skip if no data available
    #                break
    #            # Find the closest matching duration in worst-case trace
    #            closest_idx = min(
    #                range(len(worst_trace[0][cpu][task])), 
    #                key=lambda i: abs(worst_trace[0][cpu][task][i][1] - avg_duration)
    #            )
#
    #            # Adjust or remove the closest matching entry
    #            closest_timing, closest_duration = worst_trace[0][cpu][task][closest_idx]
    #            if closest_duration - avg_duration < 0:
    #                worst_trace[0][cpu][task] = (
    #                    worst_trace[0][cpu][task][:closest_idx] + 
    #                    worst_trace[0][cpu][task][closest_idx + 1:]
    #                )
    #            else:
    #                worst_trace[0][cpu][task][closest_idx] = (closest_timing, closest_duration - avg_duration)

#Used for multiprocessed map call
def get_frequency_duration_dict(file, trace_path, workload_name, combine_threads=False):
    """
    Produces a dictionary consisting of the frequency of a 
    task and the total duration on each present CPUs
        
    Args:
        file (str): The trace file name.
        trace_path (str): The path to the directory containing the trace files.
        workload_name (str): The name of the task representing the workload.
        combine_threads (bool): Controls whether or not two consecutive threads should be merged into one thread. 
            Use when traces were gathered on machine with SMT enabled

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
        combine_threads (bool): Controls whether or not two consecutive threads should be merged into one thread. 
            Use when traces were gathered on machine with SMT enabled

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
        for task, (frequency, duration) in tasks.items():
            average_dict[cpu][task] = (float(frequency/len(raw_trace_files)), int(duration//len(raw_trace_files)))
    return average_dict

def get_cpu_dict(file, trace_path, workload_name, combine_threads=False):
    """
    Parses a trace file and extracts relevant information for CPU traces.

    Args:
        file (str): The trace file name.
        trace_path (str): The path to the directory containing the trace files.
        workload_name (str): The name of the task representing the workload.
        combine_threads (bool): Controls whether or not two consecutive threads should be merged into one thread. 
            Use when traces were gathered on machine with SMT enabled

    Returns:
        tuple: A tuple containing a dictionary of CPU traces and the total duration.
    """
    # Define regular expressions for matching the total duration and the second start time
    duration_re = re.compile(r"Total Duration: (\d+\.\d+) seconds")

    # Define Regex for matching traces
    trace_regex = re.compile(
        r"\[(\d{3})\]"                      # Capture CPU ID (three digits inside square brackets)
        r".*?:\s(.*noise):\s*"                     # Lazily match everything up to 'noise:'
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
                    #TODO: Alter priority selection to be process name dependent instead. 
                    #      Example: Check against JSON file and set priority from matching process name 
                    if match[2] == "thread_noise":              # Set task priority
                        priority = 0
                    else:
                        priority = -1
                    task = match[3].rsplit(":",1)[0] or "nmi"   # Task name
                    start = int(match[4].replace(".", ""))          # Start Time (ns)
                    duration = int(match[5])                    # Duration (ns)
                    if (task == workload_name and (workload_start_time == -1 or workload_start_time > start) ):
                        workload_start_time = start
                    #Store to cpu_dict and combine threads if this is enabled to remove SMT threads
                    if combine_threads:
                        cpu_dict.setdefault(cpu_id-(cpu_id%2), {}).setdefault(task, []).append((start, duration, priority))
                    else:
                        cpu_dict.setdefault(cpu_id, {}).setdefault(task, []).append((start, duration, priority))

        m_cpu_dict: dict[int, dict[str, list[(int, int, int)]]]#= dict({'NULL': dict({'NULL': list(tuple(start,dur,prio))})})
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
                        priority = timing[2]
                        # Noise started after workload and before end
                        if start >= workload_start_time and start<=workload_start_time+total_duration:
                            adjusted_timings.append((start-workload_start_time, duration, priority))
                        # Noise started before workload but stretches past workload start
                        elif (start+duration) > workload_start_time and start<=workload_start_time+total_duration:
                            adjusted_timings.append((0, (start+duration)-workload_start_time, priority))
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
        combine_threads (bool): Controls whether or not two consecutive threads should be merged into one thread. 
            Use when traces were gathered on machine with SMT enabled
            
    Returns:
        tuple: A tuple containing a dictionary of CPU traces and the total duration.
    """

    pool = Pool()
    duration_list = pool.starmap(get_file_duration_tuple, [(file, trace_path) for file in raw_trace_files])
        
    worst_case_file, _ = max(duration_list, key=lambda x: x[1])
    print(worst_case_file)


    worst_trace = get_cpu_dict(worst_case_file, trace_path, workload_name, combine_threads)

    #if DEBUG == True:
    #    fig, ax = plt.subplots()
    #    for cpu, task_dict in worst_trace[0].items():
    #        color = iter(cm.rainbow(np.linspace(0, 1, len(task_dict.keys()))))
    #        for task, timings in task_dict.items():
    #            c = next(color)
    #            for timing in timings:
    #                ax.barh(cpu, width=timing[1], left=timing[0], color=c)
    #    plt.show()

    for cpu in worst_trace[0].keys():
        if worst_trace[0][cpu].pop(workload_name, None) != None:
            print("Workload removed")
            #del worst_trace[0][cpu][workload_name]

    #if DEBUG == True:
    #    fig, ax = plt.subplots()
    #    for cpu, task_dict in worst_trace[0].items():
    #        color = iter(cm.rainbow(np.linspace(0, 1, len(task_dict.keys()))))
    #        for task, timings in task_dict.items():
    #            c = next(color)
    #            for timing in timings:
    #                ax.barh(cpu, width=timing[1], left=timing[0], color=c)
    #    plt.show()

    return worst_trace


if __name__ == "__main__":
    main()

    
    
    



