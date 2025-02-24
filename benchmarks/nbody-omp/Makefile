#===============================================================================
# User Options
#===============================================================================

# Compiler can be set below, or via environment variable
CC        = icpx
OPTIMIZE  = yes
DEBUG     = no
DEVICE    = no
LAUNCHER  =
INJECT_NOISE = no

#===============================================================================
# Program name & source code list
#===============================================================================

program = main

source = main.cpp GSimulation.cpp

obj = $(source:.cpp=.o)

#===============================================================================
# Sets Flags
#===============================================================================

# Standard Flags
CFLAGS := $(EXTRA_CFLAGS) -std=c++17 -Wall -I../../common

# Linker Flags
LDFLAGS = -L../../common -lcommon

# Debug Flags
ifeq ($(DEBUG),yes)
  CFLAGS += -g 
  LDFLAGS  += -g
endif

# Optimization Flags
ifeq ($(OPTIMIZE),yes)
  CFLAGS += -O3 -march=native #-xCORE-AVX2 
  # TODO Fix if condition for native vs xCORE-AVX2
endif

ifeq ($(DEVICE),gpu)
  CFLAGS +=-fiopenmp -fopenmp-targets=spir64 -D__STRICT_ANSI__
else
  CFLAGS +=-qopenmp
endif

ifeq ($(INJECT_NOISE),yes)
  CFLAGS += -DNOISE
endif
#===============================================================================
# Targets to Build
#===============================================================================

$(program): $(obj)
	$(CC) $(CFLAGS) $(obj) -o $@ $(LDFLAGS)

%.o: %.cpp *.hpp
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -rf $(program) $(obj)

run: $(program)
	$(LAUNCHER) ./$(program) 10000 500
