#include <iostream>
#include <chrono>
#include <atomic>
#include <thread>
#include <cstdlib>
#include <unistd.h>
#include <iomanip>
#include <cmath>
#include "barrier_sync.h"

int cpuoccupy(double duration, double start_time, int number_of_processes) {
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

    #ifdef DEBUG
    std::cout << "Starting cpuoccupy for " << duration << " nanoseconds\n";
    #endif

    
    struct timespec start_t, rem_t;
    start_t.tv_sec = std::floor(start_time / 1000000000) ;
    start_t.tv_nsec = std::fmod(start_time, 1000000000);
    //May change this to handle small remainders by busy wait?
    while (nanosleep(&start_t, &rem_t) < 0) {
        // TODO: Make sure these are correct
        start_t.tv_sec = start_t.tv_sec - rem_t.tv_sec;
        start_t.tv_nsec = start_t.tv_nsec - rem_t.tv_nsec;
    }
        

    // Simulate CPU load with higher resolution timing
    auto end_time = std::chrono::high_resolution_clock::now() + std::chrono::duration<double,std::nano>(duration);
    while (std::chrono::high_resolution_clock::now() < end_time) {
        // Busy wait to simulate CPU load with finer resolution
        volatile double res = rand() % 1000 + 1;  // Dummy work
    }

    // Close semaphores
    cleanup_semaphores();
    #ifdef DEBUG
    std::cout << "Exiting cpuoccupy\n";
    #endif
    return EXIT_SUCCESS;
}

int main(int argc, char* argv[]) {
    double duration = 10.0;  // Default duration
    double start_time = 0.0;  // Default start time
    int number_of_processes = 1;

    // Parse arguments
    if (argc > 1) duration = std::atof(argv[1]);
    if (argc > 2) start_time = std::atof(argv[2]);
    if (argc > 3) number_of_processes = std::atoi(argv[3]);

    // Start the CPU occupy function with higher resolution
    return cpuoccupy(duration, start_time, number_of_processes);
}
