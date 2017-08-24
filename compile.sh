#!/bin/bash
cd "$(dirname "$0")"
clang-3.5	-g -std=c11 vmapi.c vm.c hostapp.c -o TaghaVM_Clang
gcc			-g -std=c11 vmapi.c vm.c hostapp.c -o TaghaVM_GCC
#-S for asm output, -g for debug, -Os for optimization by size		-pg profiling
# -Wall

#./TaghaVM_GCC
#gprof TaghaVM_GCC gmon.out > Tagha_profile.txt
