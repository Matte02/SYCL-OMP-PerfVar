#-----------------------------------------------------------------------
# This file compiles for OpenMP and MPI hybrid operations using the GNU
# compile chain.
INJECT_NOISE = yes

MINIFE_TYPES =  \
        -DMINIFE_SCALAR=double   \
        -DMINIFE_LOCAL_ORDINAL=int      \
        -DMINIFE_GLOBAL_ORDINAL=int \
	-DMINIFE_RESTRICT=__restrict__

MINIFE_MATRIX_TYPE = -DMINIFE_CSR_MATRIX
#-----------------------------------------------------------------------

#CFLAGS = -v -O3 -fiopenmp -fopenmp-targets=spir64 -D__STRICT_ANSI__\
	-ffp-contract=fast 
#	-S -emit-llvm
#\
#	-S -emit-llvm
#-mllvm -regalloc=pbqp
CFLAGS = -O3 -qopenmp

CXXFLAGS = $(CFLAGS) 

CPPFLAGS = -I. -I../utils -I../fem $(MINIFE_TYPES) -I../../../common\
	$(MINIFE_MATRIX_TYPE) #\
#	-DHAVE_MPI -DMPICH_IGNORE_CXX_SEEK \
#	-DMINIFE_REPORT_RUSAGE
ifeq ($(INJECT_NOISE),yes)
  CFLAGS += -DNOISE
endif
LDFLAGS=$(CFLAGS) -L../../../common -lcommon
LIBS=


# The MPICH_IGNORE_CXX_SEEK macro is required for some mpich versions,
# such as the one on my cygwin machine.

#CXX=mpiicpc
#CC=mpiicc

#CXX=g++
#CC=g++

CXX=icpx
CC=icc
LAUNCHER  =

#CXX=clang++
#CC=clang

#CXX=xlC
#CC=xlc

include make_targets
