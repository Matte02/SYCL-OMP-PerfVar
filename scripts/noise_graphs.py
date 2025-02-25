import re
import pandas as pd
import matplotlib.pyplot as plt
import os
import sys

def parse_data(file_path):
    # Regular expressions to extract data
    delay_pattern = re.compile(r'Core (\d+) \(Number of Noises: (\d+)\) \(Total Delay: (-\d+)\) \(Average Delay: ([\d.-]+)\) \(Max Delay: ([\d.-]+)\)')
    oversleep_pattern = re.compile(r'Core (\d+) \(Total Oversleep: (-\d+)\) \(Average Oversleep: ([\d.-]+)\) \(Max Oversleep: ([\d.-]+)\)')

    # Lists to store data
    cores = []
    num_noises = []
    total_delays = []
    avg_delays = []
    max_delays = []
    total_oversleeps = []
    avg_oversleeps = []
    max_oversleeps = []

    # Read the file
    with open(file_path, 'r') as file:
        for line in file:
            delay_match = delay_pattern.match(line)
            oversleep_match = oversleep_pattern.match(line)
            
            if delay_match:
                core, noises, total_delay, avg_delay, max_delay = delay_match.groups()
                cores.append(int(core))
                num_noises.append(int(noises))
                total_delays.append(int(total_delay))
                avg_delays.append(float(avg_delay))
                max_delays.append(float(max_delay))
            
            if oversleep_match:
                core, total_oversleep, avg_oversleep, max_oversleep = oversleep_match.groups()
                total_oversleeps.append(int(total_oversleep))
                avg_oversleeps.append(float(avg_oversleep))
                max_oversleeps.append(float(max_oversleep))

    # Create a DataFrame
    data = {
        'Core': cores,
        'Number of Noises': num_noises,
        'Total Delay': total_delays,
        'Average Delay': avg_delays,
        'Max Delay': max_delays,
        'Total Oversleep': total_oversleeps,
        'Average Oversleep': avg_oversleeps,
        'Max Oversleep': max_oversleeps
    }

    return pd.DataFrame(data)

def generate_plots(df, output_dir):
    # Group by Core and calculate mean for each core
    df_grouped = df.groupby('Core').mean().reset_index()

    # Plotting Core-Specific Data
    plt.figure(figsize=(14, 8))

    # Average Delay per Core
    plt.subplot(2, 2, 1)
    plt.bar(df_grouped['Core'], df_grouped['Average Delay'], color='blue')
    plt.title('Average Delay per Core')
    plt.xlabel('Core')
    plt.ylabel('Average Delay')

    # Max Delay per Core
    plt.subplot(2, 2, 2)
    plt.bar(df_grouped['Core'], df_grouped['Max Delay'], color='red')
    plt.title('Max Delay per Core')
    plt.xlabel('Core')
    plt.ylabel('Max Delay')

    # Average Oversleep per Core
    plt.subplot(2, 2, 3)
    plt.bar(df_grouped['Core'], df_grouped['Average Oversleep'], color='green')
    plt.title('Average Oversleep per Core')
    plt.xlabel('Core')
    plt.ylabel('Average Oversleep')

    # Max Oversleep per Core
    plt.subplot(2, 2, 4)
    plt.bar(df_grouped['Core'], df_grouped['Max Oversleep'], color='purple')
    plt.title('Max Oversleep per Core')
    plt.xlabel('Core')
    plt.ylabel('Max Oversleep')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'core_specific_plots.png'))
    plt.close()

    # Plotting Non-Core-Specific Data (Distribution Across All Cores)
    plt.figure(figsize=(14, 10))

    # Histogram of Average Delays (across all cores)
    plt.subplot(2, 2, 1)
    plt.hist(df['Average Delay'], bins=20, color='blue', edgecolor='black')
    plt.title('Distribution of Average Delays (All Cores)')
    plt.xlabel('Average Delay')
    plt.ylabel('Frequency')

    # Histogram of Max Delays (across all cores)
    plt.subplot(2, 2, 2)
    plt.hist(df['Max Delay'], bins=20, color='red', edgecolor='black')
    plt.title('Distribution of Max Delays (All Cores)')
    plt.xlabel('Max Delay')
    plt.ylabel('Frequency')

    # Histogram of Average Oversleeps (across all cores)
    plt.subplot(2, 2, 3)
    plt.hist(df['Average Oversleep'], bins=20, color='green', edgecolor='black')
    plt.title('Distribution of Average Oversleeps (All Cores)')
    plt.xlabel('Average Oversleep')
    plt.ylabel('Frequency')

    # Histogram of Max Oversleeps (across all cores)
    plt.subplot(2, 2, 4)
    plt.hist(df['Max Oversleep'], bins=20, color='purple', edgecolor='black')
    plt.title('Distribution of Max Oversleeps (All Cores)')
    plt.xlabel('Max Oversleep')
    plt.ylabel('Frequency')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'all_cores_distribution_plots.png'))
    plt.close()

def main(file_path):
    # Determine the output directory (same as the input file's directory)
    output_dir = os.path.dirname(file_path)
    if output_dir == "":
        output_dir = "."  # Use current directory if file is in the same folder

    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Parse the data
    df = parse_data(file_path)

    # Generate and save plots
    generate_plots(df, output_dir)

    print(f"Plots saved in the directory: '{output_dir}'")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python noise_graphs.py <path_to_data_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    main(file_path)