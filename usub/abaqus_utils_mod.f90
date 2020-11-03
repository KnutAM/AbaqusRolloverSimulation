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
    
    stop
    
end subroutine xit

end module abaqus_utils_mod
