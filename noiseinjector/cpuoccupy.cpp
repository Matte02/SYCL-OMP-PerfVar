#include <iostream>
#include <chrono>
#include <atomic>
#include <thread>
#include <cstdlib>
#include <unistd.h>
#include <iomanip>

#include "barrier_sync.h"

std::atomic<bool> flag(false);

int cpuoccupy(double duration, double start_time, bool verbose, int number_of_processes) {
    //Set to realtime task. May not have to change nice value
    nice(-1);
    struct sched_param sp = { .sched_priority = 50 };
    int ret = sched_setscheduler(0, SCHED_FIFO, &sp);
    if (ret == -1) {
        perror("sched_setscheduler");
        return EXIT_FAILURE;
    }

    init_semaphores();
    wait_for_barrier(number_of_processes);
    auto start = std::chrono::high_resolution_clock::now();

    if (verbose) {
        std::cout << "Starting cpuoccupy for " << duration << " seconds\n";
    }

    // Wait until the start time is reached with higher precision
    //while (std::chrono::high_resolution_clock::now() - start < std::chrono::duration<double>(start_time)) {
    //    std::this_thread::sleep_for(std::chrono::nanoseconds(1000));  // Adjust for better timing precision
    //}

    struct timespec start_t, rem_t;
    start_t.tv_sec = 0;
    start_t.tv_nsec = start_time;
    //May change this to handle small remainders by busy wait?
    while (nanosleep(&start_t, &rem_t) < 0) {
        start_t.tv_sec = start_t.tv_sec - rem_t.tv_sec;
        start_t.tv_nsec = start_t.tv_nsec - rem_t.tv_nsec;
    }

    // Simulate CPU load with higher resolution timing
    auto end_time = std::chrono::high_resolution_clock::now() + std::chrono::duration<double>(duration);
    while (std::chrono::high_resolution_clock::now() < end_time) {
        auto elapsed = std::chrono::high_resolution_clock::now() - start;

        // Adjust the utilization granularity
        if (elapsed.count() > start_time) {
            if (flag) {
                // Busy wait to simulate CPU load with finer resolution
                volatile double res = rand() % 1000 + 1;  // Dummy work
            }
        }
    }

    // Close semaphores
    cleanup_semaphores();
    std::cout << "Exiting cpuoccupy\n";
    return EXIT_SUCCESS;
}

int main(int argc, char* argv[]) {
    double duration = 10.0;  // Default duration
    double start_time = 0.0;  // Default start time
    bool verbose = false;  // Default verbosity
    int number_of_processes = 1;

    // Parse arguments
    if (argc > 1) duration = std::atof(argv[1]);
    if (argc > 2) start_time = std::atof(argv[2]);
    if (argc > 3) verbose = std::atoi(argv[3]);
    if (argc > 4) number_of_processes = std::atoi(argv[4]);

    // Start the CPU occupy function with higher resolution
    return cpuoccupy(duration, start_time, verbose, number_of_processes);
}
