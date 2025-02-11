# Define the compiler
CXX = g++
CXXFLAGS = -std=c++20 -O3 -Wall -lpthread -lrt

# Source and executable
SRC = cpuoccupy.cpp barrier_sync.cpp
EXE = cpuoccupy

# Default target
all: $(EXE)

# Debug Target
debug: CXXFLAGS += -DDEBUG
debug: $(EXE)

# Build the executable
$(EXE): $(SRC)
	$(CXX) $(CXXFLAGS) -o $(EXE) $(SRC)

# Clean up build files
clean:
	rm -f $(EXE)
