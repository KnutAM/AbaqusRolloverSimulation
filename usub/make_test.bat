@echo OFF
if not exist build (
    mkdir build
    echo * >build/.gitignore
    echo !.gitignore >>build/.gitignore
)
cd build

ifort ..\test_usub.f90 /Qmkl

cd ..