// barrier_sync.cpp
#include <semaphore.h>
#include <fcntl.h>    // For O_CREAT, O_EXCL
#include <sys/stat.h> // For mode constants
#include <cstdlib>
#include <iostream>

const char* SEM_READY = "/sem_ready";
const char* SEM_START = "/sem_start";

sem_t* ready = nullptr;
sem_t* start = nullptr;

void init_semaphores() {
    // Initialize semaphores with total_processes
    ready = sem_open(SEM_READY, O_CREAT, 0644, 0); // Initial value: 0
    start = sem_open(SEM_START, O_CREAT, 0644, 0); // Initial value: 0

    if (ready == SEM_FAILED || start == SEM_FAILED) {
        perror("sem_open");
        exit(EXIT_FAILURE);
    }
}

void wait_for_barrier(int total_processes) {
    // Signal that this process is ready
    sem_post(ready);

    // Wait until all processes are ready
    int ready_count;
    do {
        sem_getvalue(ready, &ready_count);
    } while (ready_count < total_processes); // Change "2" to total_processes dynamically when needed

    // Signal start only once all processes are ready
    sem_post(start);

    // Ensure all processes wait for the start signal
    sem_wait(start);
}

void cleanup_semaphores() {
    sem_close(ready);
    sem_close(start);
    
    // Unlink semaphores when done
    sem_unlink(SEM_READY);
    sem_unlink(SEM_START);
}
