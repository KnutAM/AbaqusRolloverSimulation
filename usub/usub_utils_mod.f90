module usub_utils_mod
implicit none
    
    private
    
    public  :: get_fid
    public  :: check_iostat
    public  :: write_node_info

    contains

    ! Use Abaqus' utility routine getoutdir to determine the full path to the base_name that resides
    ! in the current working directory. Open that file and return the file identifier. 
    function get_fid(base_name, the_action) result(file_id)
    use abaqus_utils_mod
    implicit none
        character(len=*), intent(in)            :: base_name    ! Base name for file
        character(len=*), intent(in), optional  :: the_action   ! action for open, default: 'read'
        integer                                 :: file_id      ! File identifier for file to read
        
        integer                                 :: io_status    ! Used to check that file opens 
                                                                ! sucessfully
        integer                                 :: cwd_length   ! Length of current path (used by 
                                                                ! getoutdir)
        character(len=256)                      :: filename     ! Filename (full path)
        character(len=20)                       :: int_action   ! Internal action
        
        if (present(the_action)) then
            int_action = the_action
        else
            int_action = 'read'
        endif
        
        call getoutdir(filename, cwd_length)
        
        if ((len(trim(filename)) + len(trim(base_name)) + 1) > len(filename)) then
            write(*,*) 'Current path = "'//trim(filename)//'" is too long'
            call xit()
        endif
        
        write(filename, *) trim(filename)//'/'//trim(base_name)
            
        open(newunit=file_id, file=trim(filename), iostat=io_status, action=int_action)
        call check_iostat(io_status, 'Error opening "'//base_name//'"')
        
    end function get_fid
    
    subroutine check_iostat(io_status, error_message)
    use abaqus_utils_mod
    implicit none
        integer, intent(in)             :: io_status        ! value returned by io_stat
        character(len=*), intent(in)    :: error_message    ! error message, if io_stat /= 0
        
        if (io_status /= 0) then
            write(*,*) error_message
            call xit()
        endif
    
    end subroutine
    
    subroutine write_node_info(node_label, node_coords, node_jdof, kstep, kinc)
    implicit none
        integer, intent(in)                 :: node_label
        double precision, intent(in)        :: node_coords(3)
        integer, optional, intent(in)       :: node_jdof
        integer, optional, intent(in)       :: kstep
        integer, optional, intent(in)       :: kinc
        
        write(*,"(A,I0)") 'Node label = ', node_label
        write(*,"(A,F10.5,F10.5,F10.5)") 'Node coord = ', node_coords(1), node_coords(2), node_coords(3)
        if (present(node_jdof)) then
            write(*,"(A,I0)") 'Node jdof  = ', node_jdof
        endif
        if (present(kstep)) then
            write(*,"(A,I0)") 'Step nr.   = ', kstep
        endif
        if (present(kinc)) then
            write(*,"(A,I0)") 'Increment  = ', kinc
        endif
        
    end subroutine

    
end module usub_utils_mod