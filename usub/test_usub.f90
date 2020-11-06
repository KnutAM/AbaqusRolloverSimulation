! Abaqus utility modules
include 'abaqus_utils_mod.f90'          ! Do not include when running Abaqus
!include 'abaqus_utils_dummy_mod.f90'    ! Include when running Abaqus
include 'includes.f90'

program test_usub
use find_mod
implicit none
    double precision, allocatable   :: tmp(:)
    integer, allocatable            :: tmp_int(:)
    double precision, allocatable   :: utmp(:)
    integer                         :: a2d(3,5)
    integer                         :: a1d(5)
    integer                         :: indices(2)
    
    a1d = [11, 12, 13, 14, 15]
    a2d(1,:) = [11, 12, 13, 14, 15]
    a2d(2,:) = [21, 22, 23, 24, 25]
    a2d(3,:) = [31, 32, 33, 34, 35]
    
    indices = find(a2d, 23)
    
    write(*,*) find(a1d, 13)
    write(*,*) find(a2d, 23)
    
    write(*,*) find(a2d, 0)
    
end program test_usub