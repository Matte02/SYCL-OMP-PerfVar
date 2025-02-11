import subprocess
import sys
import os
import argparse

def build_code(rebuild=False, debug=False):
    if rebuild:
        print("Forcing a rebuild...")
        subprocess.run(['make', 'clean'], check=True)
    if debug:
        subprocess.run(['make', 'debug'], check=True)
    else:
        subprocess.run(['make', 'all'], check=True)

def run_cpuoccupy(core_id, duration=10.0, start_time=0.0, verbose=False, processes=1):
    """
    Run the cpuoccupy program on a specific core with given parameters.
    """
    # Check if the core_id is valid
    if core_id < 0:
        print("Invalid core_id specified. Please use a positive core number.")
        sys.exit(1)

    # Construct the command with taskset to pin the process to the specified core
    command = f"taskset -c {core_id} ./cpuoccupy {duration} {start_time} {processes}"

    # Execute the command
    try:
        print(f"Running: {command}")
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running the command: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Run cpuoccupy with optional verbose output.")
    parser.add_argument('--duration', type=float, default=10.0, help="Duration in seconds")
    parser.add_argument('--start-time', type=float, default=0.0, help="Start time in seconds")
    parser.add_argument('--core', type=int, default=-1, help="Core ID to run on")
    parser.add_argument('--verbose', action='store_true', help="Enable verbose output")
    parser.add_argument('--rebuild', type=bool, help="Enable forced rebuild")
    parser.add_argument('--processes', type=int, help="Number of processes to wait for before executing")

    args = parser.parse_args()

    build_code(args.rebuild, args.verbose)

    # Run the cpuoccupy with provided parameters
    run_cpuoccupy(args.core, args.duration, args.start_time, args.processes)

if __name__ == "__main__":
    main()
