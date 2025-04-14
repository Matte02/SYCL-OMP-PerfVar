#include <chrono>
#include <cmath>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <unistd.h>
#include <linux/prctl.h>
#include <sys/prctl.h>
#include <time.h>
#include <signal.h>

#include "nlohmann/json.hpp"

#include <barrier_sync.h>

using json = nlohmann::json;

struct Noise {
    signed long long start_time;
    signed long long duration;
};

#ifdef USE_TIMER
static void handler(int sig, siginfo_t *si, void *uc) {
    auto caught_signal = sig; 
}
#endif
bool should_exit = false;

int cpuoccupy(const std::vector<Noise>& noises, int number_of_processes, std::string core_id) {
    //Set seed
    int seed = rand();
    auto ok = nice(-19);
    //Remove timer slack. Not tested if it actually helps.
    //int err = prctl(PR_SET_TIMERSLACK, 1L);
    //if (err == -1) {
    //    perror("set_timeslack");
    //    return EXIT_FAILURE;
    //}

    //Set to realtime task. May not have to change nice value
    #ifdef RT
    struct sched_param sp = { .sched_priority = 50 };
    int ret = sched_setscheduler(0, SCHED_FIFO, &sp);
    if (ret == -1) {
        perror("sched_setscheduler");
        return EXIT_FAILURE;
    }
    #endif

    #ifdef USE_TIMER
    timer_t timerid;
    struct sigevent sev;
    struct itimerspec its;
    struct sigaction sa;

    /* Establish handler for timer signal */
    sa.sa_flags = SA_SIGINFO;
    sa.sa_sigaction = handler;
    sigemptyset(&sa.sa_mask);
    if (sigaction(SIGRTMIN, &sa, NULL) == -1) {
        perror("sigaction");
        exit(EXIT_FAILURE);
    }

    /* Create the timer */
    sev.sigev_notify = SIGEV_SIGNAL;
    sev.sigev_signo = SIGRTMIN;
    sev.sigev_value.sival_ptr = &timerid;
    //Test accuracy with different clocks?
    if (timer_create(CLOCK_MONOTONIC, &sev, &timerid) == -1) {
        perror("timer_create");
        exit(EXIT_FAILURE);
    }
    #endif

    init_semaphores();

    // Sync up all processes to start at the same time.
    wait_for_barrier(number_of_processes);
    #ifdef LOOP
    while(!should_exit){
    #endif
        auto total_delay = 0;
        auto max_delay = 0;
        auto max_oversleep = 0;
        auto total_oversleep = 0;
        auto sleeps = 0;
        struct timespec start_t, rem_t;
        // Record the program's absolute start time
        auto program_start_time = std::chrono::high_resolution_clock::now();

        for (const auto& noise : noises) { 
            if(should_exit){
                break;
            }       
            // Calculate relative wait time for this noise
            auto current_time = std::chrono::high_resolution_clock::now();
            auto wait_time = std::chrono::duration<signed long long, std::nano>(noise.start_time) -
                            std::chrono::duration_cast<std::chrono::duration<double, std::nano>>(current_time - program_start_time);

            // Sleep until the start time for this noise
            if (wait_time.count() > 0) {

                #ifdef USE_TIMER
                /* Start the timer */
                its.it_value.tv_sec = std::floor(wait_time.count() / 1e9);
                its.it_value.tv_nsec = std::fmod(wait_time.count(), 1e9);
                its.it_interval.tv_sec = its.it_value.tv_sec;
                its.it_interval.tv_nsec = its.it_value.tv_nsec;
                if (timer_settime(timerid, 0, &its, NULL) == -1) {
                    perror("timer_settime");
                    std::cout << "E" <<std::endl;
                    exit(EXIT_FAILURE);
                }
                //Pause until SIGCONT
                pause();

                #else

                start_t.tv_sec = std::floor(wait_time.count() / 1e9);
                start_t.tv_nsec = std::fmod(wait_time.count(), 1e9);
                //while (clock_nanosleep(CLOCK_MONOTONIC, 0, &start_t, &rem_t) != 0) {
                while (nanosleep(&start_t, &rem_t) != 0) {
                    start_t.tv_sec = rem_t.tv_sec;
                    start_t.tv_nsec = rem_t.tv_nsec;
                }
                #ifdef DEBUG
                sleeps++;
                auto wakeup_delay = std::chrono::duration<signed long long, std::nano>(noise.start_time) -
                            std::chrono::duration_cast<std::chrono::duration<double, std::nano>>(std::chrono::high_resolution_clock::now() - program_start_time);
                if(wakeup_delay.count() > 0) {
                    std::cout << "Core " << core_id << "CPU OCCUPY WOKE UP TOO SOON: " << wakeup_delay.count() << std::endl;
                } else {
                    total_oversleep += wakeup_delay.count();
                    max_oversleep = (wakeup_delay.count() < max_oversleep) ? wakeup_delay.count() : max_oversleep;  
                }
                #endif
                #endif
            } else {
                //Count amount of time current time overshoots noise start_time
                max_delay = (wait_time.count() < max_delay) ? wait_time.count() : max_delay;
                total_delay += wait_time.count();
            }

            // Simulate CPU load for this noise duration
            current_time = std::chrono::high_resolution_clock::now();
            auto end_time = std::chrono::duration<signed long long, std::nano>(noise.duration) + current_time;

            while (std::chrono::high_resolution_clock::now() < end_time) {
                volatile double work = seed % 1000 + 1; // Dummy work
            }
        }
    #ifdef DEBUG
    std::cout << "Core " << core_id 
        << " (Number of Noises: " << noises.size() 
        << ") (Total Delay: " << total_delay 
        << ") (Average Delay: " << static_cast<double>(total_delay) / noises.size() 
        << ") (Max Delay: " << max_delay 
        << ")" <<std::endl;
    
    std::cout << "Core " << core_id 
        << " (Total Oversleep: " << total_oversleep 
        << ") (Average Oversleep: " << static_cast<double>(total_oversleep)/sleeps 
        << ") (Max Oversleep: " << max_oversleep 
        << ")" << std::endl;
    #endif
    #ifdef LOOP
    }
    #endif
    while(!should_exit){
        pause();
    }
    // Close semaphores
    cleanup_semaphores();
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
        Noise previous = {-1,-1};
        for (const auto& entry : config[core_id]) {
            Noise noise = {entry[0].get<signed long long>(), entry[1].get<signed long long>()};
            if (previous.start_time < noise.start_time) {
                noise_schedule.push_back(noise);
                
            } else {
                std::cerr << "Error (" << core_id << "): Noise not in cronological order. Previous Noise start: " << previous.start_time << "Current Start Time: "<<noise.start_time <<  std::endl;
            }
            previous = noise;
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

void termHandler( int signum ) {
    should_exit = true;
    std::cout << "KILL" <<std::endl;
    cleanup_semaphores();
    exit(0);
}

int main(int argc, char* argv[]) {
    if (argc < 4) {
        std::cerr << "Usage: " << argv[0] << " <json_file> <core_id> <number_of_processes>" << std::endl;
        return EXIT_FAILURE;
    }
    signal(SIGTERM, termHandler);  

    std::string json_file = argv[1];
    std::string core_id = argv[2];
    int number_of_processes = std::stoi(argv[3]);


    std::vector<Noise> noises_schedule;
    if (parseJSON(noises_schedule, json_file, core_id)) {
        // Failed parsing JSON file.
        return EXIT_FAILURE;
    }

    // Start the CPU occupy function with higher resolution
    return cpuoccupy(noises_schedule, number_of_processes, core_id);
}
