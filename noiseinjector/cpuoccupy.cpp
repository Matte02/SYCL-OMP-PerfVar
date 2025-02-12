#include <chrono>
#include <cmath>
#include <cstdlib>
#include <fstream>
#include <iostream>

#include <unistd.h>

#include "nlohmann/json.hpp"

#include "barrier_sync.h"

using json = nlohmann::json;

struct Noise {
    double start_time;
    double duration;
};

int cpuoccupy(const std::vector<Noise>& noises, int number_of_processes) {
    //Set to realtime task. May not have to change nice value
    nice(-1);
    struct sched_param sp = { .sched_priority = 50 };
    int ret = sched_setscheduler(0, SCHED_FIFO, &sp);
    if (ret == -1) {
        perror("sched_setscheduler");
        return EXIT_FAILURE;
    }

    init_semaphores();
    // Sync up all processes to start at the same time.
    wait_for_barrier(number_of_processes);


    // Record the program's absolute start time
    auto program_start_time = std::chrono::high_resolution_clock::now();


    for (const auto& noise : noises) {
        // Calculate relative wait time for this noise
        auto current_time = std::chrono::high_resolution_clock::now();
        auto wait_time = std::chrono::duration<double, std::nano>(noise.start_time) -
                         std::chrono::duration_cast<std::chrono::duration<double, std::nano>>(current_time - program_start_time);

        // Sleep until the start time for this noise
        if (wait_time.count() > 0) {
            struct timespec start_t, rem_t;
            start_t.tv_sec = std::floor(wait_time.count() / 1e9);
            start_t.tv_nsec = std::fmod(wait_time.count(), 1e9);

            while (nanosleep(&start_t, &rem_t) < 0) {
                start_t.tv_sec = rem_t.tv_sec;
                start_t.tv_nsec = rem_t.tv_nsec;
            }
        }

        // Simulate CPU load for this noise duration
        auto end_time = std::chrono::high_resolution_clock::now() + 
                        std::chrono::duration<double, std::nano>(noise.duration);
        while (std::chrono::high_resolution_clock::now() < end_time) {
            volatile double res = rand() % 1000 + 1; // Dummy work
        }
    }

    // Close semaphores
    cleanup_semaphores();
    #ifdef DEBUG
    std::cout << "Exiting cpuoccupy\n";
    #endif
    return EXIT_SUCCESS;
}

int parseJSON(std::vector<Noise>& noise_schedule, const std::string& json_file, const std::string& core_id) {
    // Load the JSON file
    std::ifstream file(json_file);
    if (!file.is_open()) {
        std::cerr << "Error: Unable to open JSON file: " << json_file << std::endl;
        return EXIT_FAILURE;
    }

    json config;
    file >> config;
    file.close();

    if (config.contains(core_id)) {
        for (const auto& entry : config[core_id]) {
            Noise noise = { entry["start_time"].get<double>(), entry["duration"].get<double>() };
            noise_schedule.push_back(noise);
        }
    } else {
        // Should this casue an error? Or should it just continue with an empty noise schedule?
        // It should be fine to keep this, as we should only be starting a cpuoccupy process, if it has noise to inject on this core.
        // Might help us catch bugs, if run_noise is wrongly implemented.
        std::cerr << "Error: Core ID " << core_id << " not found in JSON file." << std::endl;
        return EXIT_FAILURE;
    }
    return EXIT_SUCCESS;
}

int main(int argc, char* argv[]) {
    if (argc < 4) {
        std::cerr << "Usage: " << argv[0] << " <json_file> <core_id> <number_of_processes>" << std::endl;
        return EXIT_FAILURE;
    }

    std::string json_file = argv[1];
    std::string core_id = argv[2];
    int number_of_processes = std::stoi(argv[3]);


    std::vector<Noise> noises_schedule;
    if (parseJSON(noises_schedule, json_file, core_id)) {
        // Failed parsing JSON file.
        return EXIT_FAILURE;
    }

    // Start the CPU occupy function with higher resolution
    return cpuoccupy(noises_schedule, number_of_processes);
}
