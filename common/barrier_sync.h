// barrier_sync.h
#ifndef BARRIER_SYNC_H
#define BARRIER_SYNC_H

void init_semaphores();
void wait_for_barrier(int total_processes);
void cleanup_semaphores();

#endif // BARRIER_SYNC_H
