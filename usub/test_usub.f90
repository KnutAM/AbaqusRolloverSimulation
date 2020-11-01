include 'abaqus_utils_mod.f90'
include 'usub_utils_mod.f90'
include 'uel_stiff_mod.f90'

module tmp_mod
implicit none

    contains
    
subroutine print_stiffness()
use uel_stiff_mod
implicit none
    
    if (not(allocated(uel_stiffness))) then
        write(*,*) 'Allocating uel stiffness'
        call allocate_uel_stiffness(1.d0)
    endif
    
    write(*, *) uel_stiffness(1:3, 1)
    
end subroutine

end module


program test_usub
use tmp_mod
implicit none

    write(*,*) 'Call nr 1'
    call print_stiffness()
    
    write(*,*) 'Call nr 2'
    call print_stiffness()
    

end program test_usub