# Common Makefile

# Compiler and flags
CC = g++
CXXFLAGS = -O3 -std=c++17 -I. -DBARRIER_TIMEOUT # Include current directory for shared headers
LDFLAGS = 

# Check if BUSY_WAIT should be defined
ifneq ($(filter 1 yes true,$(USE_BUSY_WAIT)),)
    CXXFLAGS += -DBUSY_WAIT
endif

# Shared source files
SRC = barrier_sync.cpp
OBJS = $(SRC:.cpp=.o)
STATIC_LIB = libcommon.a

# Default target: build static library
all: $(STATIC_LIB)

# Create static library from object files
$(STATIC_LIB): $(OBJS)
	ar rcs $@ $^

# Compile rule
%.o: %.cpp %.h
	$(CC) $(CXXFLAGS) -c $< -o $@

# Clean up
clean:
	rm -f $(OBJS) $(STATIC_LIB)
