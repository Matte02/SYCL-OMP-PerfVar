import subprocess
import sys
import os
import argparse
import signal
import atexit
import time

NOISE_INJECTOR_FOLDER_PATH = "../noiseinjector"

def build_code(rebuild=False, debug=False):
    # Change the current working directory to the noise injector folder
    os.chdir(NOISE_INJECTOR_FOLDER_PATH)
    
    if rebuild:
        print("Forcing a rebuild...")
        subprocess.run( ['make', 'clean'], check=True)
    if debug:
        subprocess.run(['make', 'debug'], check=True)
    else:
        subprocess.run(['make', 'all'], check=True)

def run_cpuoccupy_parallel(json_file, verbose=False, no_benchmark=False, any_core=False):
    """
    Run cpuoccupy processes in parallel, one for each core defined in the JSON file.
    """
    # Check if the JSON file exists
    if not os.path.exists(json_file):
        print(f"Error: JSON file not found: {json_file}")
        sys.exit(1)

    # Parse the JSON file to get core IDs
    import json
    with open(json_file, 'r') as f:
        config = json.load(f)

    core_ids = config.keys()


    # Get the number of available CPU cores
    available_cores = os.cpu_count()
    if available_cores is None:
        print("Error: Unable to determine the number of available CPU cores.")
        sys.exit(1)

    # Check if the number of cores in the JSON exceeds available cores
    num_cores_in_json = len(core_ids)
    
    if num_cores_in_json > available_cores:
        print(f"Error: The JSON file specifies {num_cores_in_json} cores, but only {available_cores} cores are available on this system.")
        sys.exit(1)

    # Check that all core IDs in the JSON file are within the available cores range
    for core_id in core_ids:
        if int(core_id) >= available_cores:
            print(f"Error: Core ID {core_id} is invalid. This system has only {available_cores} cores.")
            sys.exit(1)

    num_processes = len(core_ids) if no_benchmark else len(core_ids) + 1
    print(f"Num of processes (should be number of cores({num_cores_in_json}) + 1): {num_processes}")
    for core_id in core_ids:
        # Construct the command for taskset
        command = f"./{NOISE_INJECTOR_FOLDER_PATH}/cpuoccupy {json_file} {core_id} {num_processes}"
        if not any_core: 
            command = f"taskset -c {core_id} " + command

        if verbose:
            print(f"Starting: {command}")

        # Start the process in parallel
        try:
            process = subprocess.Popen(command, shell=True, preexec_fn=os.setsid)
            processes_list.append((process, core_id))
        except Exception as e:
            print(f"Failed to start process on core {core_id}: {e}")
            sys.exit(1)

    # Wait for all processes to finish
    for process, core_id in processes_list:
        process.wait()
        if verbose:
            print(f"Process on core {core_id} finished.")

processes_list = []
def cleanup(signum, frame):
    print("CLEANUP")
    for p, coreid in processes_list:
        os.killpg(os.getpgid(p.pid), signal.SIGTERM)
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="Run cpuoccupy on multiple cores in parallel using a single JSON configuration.")
    parser.add_argument('--json-file', type=str, default="noise_config.json", help="JSON file containing noise configurations")
    parser.add_argument('--verbose', action='store_true', help="Enable verbose output")
    parser.add_argument('--rebuild', action='store_true', help="Force rebuild of the project")
    parser.add_argument('--debug', action='store_true', help="Build in debug mode")
    parser.add_argument('--no-benchmark', action='store_true', help="Whether to wait for benchmarks sync signal or not. This should be enabled if running without benchmark.")
    parser.add_argument('--any-core', action='store_true', help="Whether the noise should run on any core (if this option isn't selected the noise will run on specified core only).")

    args = parser.parse_args()

    # Step 1: Build the code
    build_code(args.rebuild, args.debug)

    # Step 2: Run all cpuoccupy processes in parallel
    run_cpuoccupy_parallel(args.json_file, args.verbose, args.no_benchmark, args.any_core)

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, cleanup)
    main()

