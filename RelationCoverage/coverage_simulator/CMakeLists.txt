cmake_minimum_required(VERSION 3.22)

project(coverage_simulator)

add_library(coverage_simulator SHARED coverage_simulator.c)
find_package(DynamoRIO)
if (NOT DynamoRIO_FOUND)
    message(FATA_ERROR "DynamoRIO package required to build")
endif(NOT DynamoRIO_FOUND)

configure_DynamoRIO_client(coverage_simulator)