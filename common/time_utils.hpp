#ifndef TIME_UTILS_HPP
#define TIME_UTILS_HPP

#include <ctime>
#include <iostream>
#include <iomanip>

struct Timer {
    struct timespec start_time, end_time;

    Timer() {
        clock_gettime(CLOCK_MONOTONIC_RAW, &start_time);
    }

    // Stops the timer and records the end time
    void stop() {
        clock_gettime(CLOCK_MONOTONIC_RAW, &end_time);
    }

    // Returns elapsed time in seconds with nanosecond precision
    double elapsed() const {
        return (end_time.tv_sec - start_time.tv_sec) + (end_time.tv_nsec - start_time.tv_nsec) / 1e9;
    }

    // Helper function to format and print timestamps
    static void print_time(const std::string& label, const struct timespec& ts) {
        std::cout << label << ": " << ts.tv_sec << "." 
                  << std::setw(9) << std::setfill('0') << ts.tv_nsec << " seconds" << std::endl;
    }

    // Prints start, end, and duration
    void print(const std::string& label = "Elapsed time") const {
        print_time("Start time", start_time);
        print_time("End time", end_time);
        std::cout << label << ": " << std::fixed << std::setprecision(9) << elapsed() << " seconds" << std::endl;
    }
};

#endif // TIME_UTILS_HPP
