#include <iostream>

import argparse;

int main(int ac, char** av) {
    argparse::ArgumentParser parser(av[0]);
    
    parser.add_argument("--test").flag();
    try {
        parser.parse_args(ac, av);
    } catch (const std::exception& e) {
        std::cerr << e.what() << std::endl;
        return 1;
    }

    return 0;
}