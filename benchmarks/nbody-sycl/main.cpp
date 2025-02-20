//==============================================================
// Copyright © 2020 Intel Corporation
//
// SPDX-License-Identifier: MIT
// =============================================================

#include "GSimulation.hpp"
#include <iostream>
#include <chrono>
#include "barrier_sync.h"

int main(int argc, char** argv) {
  #ifdef NOISE
  if (argc == 4) {
    int num_of_other_processes = std::atoi(argv[3]);
    init_semaphores();
    wait_for_barrier(num_of_other_processes + 1);
  }
  else {
    std::cerr << "Expected number of other processes to wait for last command line argument." << std::endl;
    return 1;
  }
  #endif
  struct timespec ts_start;
  clock_gettime(CLOCK_MONOTONIC_RAW, &ts_start);

  int n;      // number of particles
  int nstep;  // number ot integration steps

  GSimulation sim;

  if (argc > 1) {
    n = std::atoi(argv[1]);
    sim.SetNumberOfParticles(n);
    if (argc >= 3) {
      nstep = std::atoi(argv[2]);
      sim.SetNumberOfSteps(nstep);
    }
  }

  sim.Start();

  struct timespec ts_end;
  clock_gettime(CLOCK_MONOTONIC_RAW, &ts_end); // Change to RAW?

  // Calculate duration 
  struct timespec duration;
  duration.tv_sec = ts_end.tv_sec - ts_start.tv_sec;
  duration.tv_nsec = ts_end.tv_nsec - ts_start.tv_nsec;

  // Normalize the nanoseconds field
  // Move to common folder? And make it a utils function?
  // TODO: Cannot handle sub 0.1s durations. Results in faulty duration eg 0.04 becomes 0.4
  if (duration.tv_nsec < 0) {
      duration.tv_sec -= 1;
      duration.tv_nsec += 1'000'000'000;
  }


  // Wait with prints untill after the benchmark is done. 
  std::cout << "Start time: "<< ts_start.tv_sec << "." << ts_start.tv_nsec << std::endl;
  std::cout << "End time: "<< ts_end.tv_sec << "." << ts_end.tv_nsec << std::endl;
  std::cout << "Duration: " << duration.tv_sec << "." << duration.tv_nsec << std::endl;

  #ifdef NOISE
  cleanup_semaphores();
  #endif

  return 0;
}
