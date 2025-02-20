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

#ifdef BARRIER_TIMEOUT
#define TIMEOUT_SECONDS 10
bool passed_barrier = false;
static void timeout_handler(int sig, siginfo_t *si, void *uc) {
    auto caught_signal = sig;
    if (!passed_barrier) {
        cleanup_semaphores();
        exit(EXIT_FAILURE);
    }  
}
#endif

int cpuoccupy(const std::vector<Noise>& noises, int number_of_processes) {
    //Set seed
    int seed = rand();
    //Remove timer slack. Not tested if it actually helps.
    int err = prctl(PR_SET_TIMERSLACK, 1L);
    if (err == -1) {
        perror("set_timeslack");
        return EXIT_FAILURE;
    }

    //Set to realtime task. May not have to change nice value
    //auto ok = nice(-1);
    struct sched_param sp = { .sched_priority = 50 };
    int ret = sched_setscheduler(0, SCHED_FIFO, &sp);
    if (ret == -1) {
        perror("sched_setscheduler");
        return EXIT_FAILURE;
    }

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

    #ifdef BARRIER_TIMEOUT
    timer_t timeoutid;
    struct sigevent sevt;
    struct itimerspec itst;
    struct sigaction sat;

    /* Establish handler for timeout signal */
    sat.sa_flags = SA_SIGINFO;
    sat.sa_sigaction = timeout_handler;
    sigemptyset(&sat.sa_mask);
    if (sigaction(SIGRTMAX, &sat, NULL) == -1) {
        perror("sigaction");
        exit(EXIT_FAILURE);
    }

    /* Create the timer */
    sevt.sigev_notify = SIGEV_SIGNAL;
    sevt.sigev_signo = SIGRTMAX;
    sevt.sigev_value.sival_ptr = &timeoutid;
    if (timer_create(CLOCK_MONOTONIC, &sevt, &timeoutid) == -1) {
        perror("timeout_create");
        exit(EXIT_FAILURE);
    }
    /* Start the timer */
    itst.it_value.tv_sec = TIMEOUT_SECONDS;
    itst.it_value.tv_nsec = 0;
    itst.it_interval.tv_sec = itst.it_value.tv_sec;
    itst.it_interval.tv_nsec = itst.it_value.tv_nsec;
    if (timer_settime(timeoutid, 0, &itst, NULL) == -1) {
        perror("timer_settime");
        exit(EXIT_FAILURE);
    }
    #endif

    // Sync up all processes to start at the same time.
    wait_for_barrier(number_of_processes);

    #ifdef BARRIER_TIMEOUT
    passed_barrier = true;
    if (timer_delete(timeoutid) == -1) {
        perror("timer_delete");
        exit(EXIT_FAILURE);
    }
    #endif

    // Record the program's absolute start time
    auto program_start_time = std::chrono::high_resolution_clock::now();
    auto prev = 0;
    auto i = 0;
    auto total_delay = 0;
    struct timespec start_t, rem_t;

    for (const auto& noise : noises) {
        i++;
        if (prev>=noise.start_time){
            exit(EXIT_FAILURE);
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
            #endif
        } else {
            //Count amount of time current time overshoots noise start_time
            total_delay += wait_time.count();
        }

        // Simulate CPU load for this noise duration
        auto end_time = std::chrono::duration<signed long long, std::nano>(noise.start_time) + 
                        std::chrono::duration<signed long long, std::nano>(noise.duration) + program_start_time;
                        
        if (end_time > std::chrono::duration<signed long long, std::nano>(noise.duration) + program_start_time) {
            end_time = std::chrono::duration<signed long long, std::nano>(noise.duration) + program_start_time;
        }

        while (std::chrono::high_resolution_clock::now() < end_time) {
            volatile double res = seed % 1000 + 1; // Dummy work
        }
        prev = noise.start_time;
    }
    // Close semaphores
    cleanup_semaphores();
    #ifdef DEBUG
    std::cout << "Exiting cpuoccupy\n";
    std::cout << noises.size() <<std::endl;
    std::cout << i <<std::endl;
    std::cout << total_delay <<std::endl;
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
            Noise noise = {entry[0].get<signed long long>(), entry[1].get<signed long long>()};
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
