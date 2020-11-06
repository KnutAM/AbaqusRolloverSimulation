! Use this module for debugging without calling via abauqs. Add utility functions with the minimum
! required functionality allowing debugging
module abaqus_utils_mod
implicit none

    contains
    
subroutine getoutdir(cwd, cwd_length)
implicit none
    integer, intent(out)            :: cwd_length   ! Length of current path
    character(len=256), intent(out) :: cwd          ! Current working directory
    
    call getcwd(cwd)
    
    cwd_length = len(trim(cwd))
    
end subroutine getoutdir

subroutine xit()
implicit none
    write(*,*) 'xit was called, quiting with error code 1'
    error stop 1
    
end subroutine xit

subroutine posfil(nstep,ninc,array,jrdc)
implicit none
    integer, intent(in)             :: nstep
    integer, intent(in)             :: ninc
    double precision, intent(inout) :: array(:)
    integer, intent(out)            :: jrdc
    
    array(1) = transfer(2000, 1.d0)
    
    jrdc = 0
    
end subroutine

subroutine dbfile(lop, array, jrdc)
implicit none
    integer, intent(in)             :: lop
    double precision, intent(inout) :: array(:)
    integer, intent(out)            :: jrdc
    
    array(1) = transfer(2000, 1.d0)
    
    jrdc = 0
    
end subroutine

end module abaqus_utils_mod
