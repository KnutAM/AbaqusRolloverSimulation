include 'abaqus_utils_mod.f90'
!include 'usub_utils_mod.f90'
!include 'uel_stiff_mod.f90'
include 'sort_mod.f90'

module tmp_mod
implicit none

    contains
    
end module


program test_usub
use sort_mod
implicit none
    double precision, allocatable   :: tmp(:)
    integer, allocatable            :: tmp_int(:)
    double precision, allocatable   :: utmp(:)
    
    
    allocate(tmp, source=[1.d0,4.d0,2.d0,2.1d0])
    
    allocate(tmp_int, source=[1, -3, 6, 2])
    
    write(*,*) 'tmp_dbl'
    write(*,*) tmp
    call unique(tmp, utmp, 0.2d0)
    write(*,*) utmp
    call unique(tmp, utmp)
    write(*,*) utmp
    

end program test_usub