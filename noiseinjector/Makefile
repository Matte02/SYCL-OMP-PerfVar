# Define the compiler
CXX = g++
CXXFLAGS = -std=c++20 -O3 -Wall  -Iinclude -I../common -DDEBUG
LDFLAGS = -lpthread -lrt

# Shared library (built by common/)
COMMON_DIR = ../common
COMMON_LIB = $(COMMON_DIR)/libcommon.a

# Check if REAL_TIME should be defined
ifneq ($(filter 1 yes true,$(REAL_TIME)),)
    CXXFLAGS += -DRT
endif

# Source and executable
SRC = cpuoccupy.cpp
EXE = cpuoccupy

# Default target
all: $(EXE)

# Link the benchmark with the static library
$(EXE): $(SRC) $(COMMON_LIB)
	$(CXX) $(CXXFLAGS) $^ -o $@ $(LDFLAGS)

# Debug Target
debug: CXXFLAGS += -DDEBUG
debug: $(EXE)

# Clean up build files
clean:
	rm -f $(EXE)
