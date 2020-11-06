@echo OFF
if not exist build (
    mkdir build
)
cd build

ifort ..\test_usub.f90 /Qmkl

cd ..