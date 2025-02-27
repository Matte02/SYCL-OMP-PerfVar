//==============================================================
// Copyright © 2020 Intel Corporation
//
// SPDX-License-Identifier: MIT
// =============================================================

#include "GSimulation.hpp"
#include <iostream>
#include <chrono>
#include "barrier_sync.h"
#include "time_utils.hpp"

int main(int argc, char** argv) {
  #ifdef NOISE
  cleanup_semaphores();
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
  Timer total_timer;

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

  total_timer.stop();
  total_timer.print("Total Duration");

  #ifdef NOISE
  cleanup_semaphores();
  #endif

  return 0;
}
