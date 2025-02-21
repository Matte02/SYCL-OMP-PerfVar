// barrier_sync.cpp
#include "barrier_sync.h"
#include <semaphore.h>
#include <fcntl.h>    // For O_CREAT, O_EXCL
#include <sys/stat.h> // For mode constants
#include <cstdlib>
#include <iostream>
#include <time.h>
#include <signal.h>

const char* SEM_READY = "/sem_ready";
const char* SEM_START = "/sem_start";

sem_t* ready = nullptr;
sem_t* start = nullptr;

#ifdef BARRIER_TIMEOUT
#define TIMEOUT_SECONDS 10
bool passed_barrier = false;
timer_t timeoutid; // Make this global
static void timeout_handler(int sig, siginfo_t *si, void *uc) {
    auto caught_signal = sig;
    std::cerr << "Timeout occurred: Process did not reach the barrier in time." << std::endl;
    if (!passed_barrier) {
        cleanup_semaphores();
        exit(EXIT_FAILURE);
    }  
}
#endif

void init_semaphores() {
    // Initialize semaphores with total_processes
    ready = sem_open(SEM_READY, O_CREAT, 0644, 0); // Initial value: 0
    start = sem_open(SEM_START, O_CREAT, 0644, 0); // Initial value: 0

    if (ready == SEM_FAILED || start == SEM_FAILED) {
        perror("sem_open");
        exit(EXIT_FAILURE);
    }

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
}

void wait_for_barrier(int total_processes) {
    // Signal that this process is ready
    sem_post(ready);

    // Wait until all processes are ready
    int ready_count;
    do {
        sem_getvalue(ready, &ready_count);
    } while (ready_count < total_processes);

    // Signal start only once all processes are ready
    sem_post(start);

    // Ensure all processes wait for the start signal
    sem_wait(start);

    #ifdef BARRIER_TIMEOUT
    passed_barrier = true;
    if (timer_delete(timeoutid) == -1) {
        perror("timer_delete");
        exit(EXIT_FAILURE);
    }
    #endif
}

void cleanup_semaphores() {
    sem_close(ready);
    sem_close(start);
    
    // Unlink semaphores when done
    sem_unlink(SEM_READY);
    sem_unlink(SEM_START);
}