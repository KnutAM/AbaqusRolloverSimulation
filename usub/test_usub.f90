! Abaqus utility modules
include 'abaqus_utils_mod.f90'          ! Do not include when running Abaqus
!include 'abaqus_utils_dummy_mod.f90'    ! Include when running Abaqus
! fortran-utilities modules
include 'utils/src/resize_array_mod.f90'
include 'utils/src/sort_mod.f90'
include 'utils/src/find_mod.f90'
include 'utils/src/linalg_mod.f90'
! Rollover modules
include 'usub_utils_mod.f90'
include 'filenames_mod.f90'
include 'step_type_mod.f90'
include 'uel_stiff_mod.f90'
include 'uel_trans_mod.f90'
include 'node_id_mod.f90'
include 'bc_mod.f90'
include 'load_param_mod.f90'
include 'disp_mod.f90'
include 'urdfil_mod.f90'

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