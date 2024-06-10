#include <vector>
#include <string>
#include <iostream>
#include <chrono>
#include <stdexcept>
#include <sstream>

#ifndef WIN32_LEAN_AND_MEAN
#   define WIN32_LEAN_AND_MEAN 1
#endif
#pragma warning(push)
#pragma warning(disable: 5039)
#include <windows.h>
#pragma warning(pop)
#include <assert.h>

struct CTRL_C {
    inline static std::atomic<bool> requested = false;
    
    CTRL_C() {
        BOOL _Ready = SetConsoleCtrlHandler(&_Windows_Console_Ctrl_Handler, TRUE);
        assert(_Ready);
    }

    static BOOL WINAPI _Windows_Console_Ctrl_Handler(DWORD fdwCtrlType) noexcept
    {
        try {
            switch (fdwCtrlType) {
                // Handle the CTRL-C signal.
            case CTRL_C_EVENT:
                CTRL_C::requested = true;
                return TRUE;

            case CTRL_CLOSE_EVENT:
                return FALSE;

            case CTRL_BREAK_EVENT:
                CTRL_C::requested = true;
                return TRUE;

            case CTRL_LOGOFF_EVENT:
                return FALSE;

            case CTRL_SHUTDOWN_EVENT:
                return FALSE;

            default:
                return FALSE;
            }
        } catch (...) {
            return FALSE;
        }
    }
};


import argparse;
import fswatch;

int main(int ac, char** av) {
    try {
        std::vector<std::string> paths;
        fswatch::Configuration conf;
        {
            argparse::ArgumentParser argparser(av[0]);
            
            argparser.add_argument("paths")
                .help("paths to watch")
                .append()
                .store_into(paths);

            argparser.add_argument("--recurse", "-r")
                .help("watch directories recursively")
                .flag();

            argparser.add_argument("--latency", "-l")
                .help("polling events interval in milliseconds")
                .scan<'u', uint32_t>()
                .default_value(500);

            try {
                argparser.parse_args(ac, av);
            } catch (const std::exception& e) {
                std::cerr << e.what() << std::endl;
                std::cerr << argparser;
                return 1;
            }

            conf.latency = std::chrono::milliseconds{argparser.get<uint32_t>("--latency")};
        }

        // create service
        fswatch::Service service(paths, conf);
        
        // start service
        service.start();

        CTRL_C ctrl_c;
        // read events
        while (!CTRL_C::requested) {
            if (service.wait_events_for(std::chrono::seconds{1})) {
                std::vector<fswatch::Event> events = service.pop_events();
                for (const auto& event : events) {
                    std::cout << event.to_string() << std::endl;
                }
            }
        }

        // stop service
        service.reset();
        
        // unwrap exception from watcher thread
        service.rethrow();
        
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "ERROR: in main: " << e.what() << std::endl;
        return 1;
    }
}
