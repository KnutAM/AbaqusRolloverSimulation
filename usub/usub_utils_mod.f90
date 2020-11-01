module usub_utils_mod
implicit none

contains 

! Use Abaqus' utility routine getoutdir to determine the full path to the base_name that resides
! in the current working directory. Open that file and return the file identifier. 
subroutine get_fid(base_name, file_id)
!use abaqus_utils_mod, only : getoutdir, xit
implicit none
    character(len=*), intent(in):: base_name    ! Base name for file
    integer, intent(out)        :: file_id      ! File identifier for file to read
    
    integer                     :: io_status    ! Used to check that file opens sucessfully
    integer                     :: cwd_length   ! Length of current path (used by getoutdir)
    character(len=256)          :: filename     ! Filename (full path)
    
    call getoutdir(filename, cwd_length)
    
    if ((len(trim(filename)) + len(trim(base_name)) + 1) > len(filename)) then
        write(*,*) 'Current path = "'//trim(filename)//'" is too long'
        call xit()
    endif
    
    write(filename, *) trim(filename)//'/'//trim(base_name)
        
    open(newunit=file_id, file=trim(filename), iostat=io_status, action='read')
    if (io_status /= 0) then
        write(*,*) 'Error opening '//base_name
        call xit()
    endif
    
end subroutine get_fid

end module usub_utils_mod