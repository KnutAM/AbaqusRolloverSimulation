module usub_utils_mod
implicit none
    
    private
    
    public  :: get_fid
    public  :: get_step_type
    public  :: STEP_TYPE_INITIAL_DEPRESSION
    public  :: STEP_TYPE_ROLLING
    public  :: STEP_TYPE_MOVE_BACK
    public  :: STEP_TYPE_REAPPLY_LOAD
    public  :: STEP_TYPE_RELEASE_NODES
    
    ! Constants for the get_step_type function:
    integer, parameter  :: STEP_TYPE_INITIAL_DEPRESSION = -1
    integer, parameter  :: STEP_TYPE_ROLLING = 0
    integer, parameter  :: STEP_TYPE_MOVE_BACK = 1
    integer, parameter  :: STEP_TYPE_REAPPLY_LOAD = 2
    integer, parameter  :: STEP_TYPE_RELEASE_NODES = 3

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
    
    function get_step_type(kstep) result (step_type)
    ! Determine the step type for the given step number, see module constant
    implicit none
        integer, parameter  :: N_STEP_INITIAL = 2   ! Number of initial steps including first rollover
        integer, parameter  :: N_STEP_PER_CYCLE = 4 ! Number of steps per rollover cycle
        
        integer, intent(in) :: kstep                ! Step number
        integer             :: step_type            ! Step type
        
        if (kstep < N_STEP_INITIAL) then
            step_type = -kstep
        else
            step_type = mod(kstep-N_STEP_INITIAL, N_STEP_BETWEEN)
        endif
        
        ! Check result
        if (not(any(step_type == [STEP_TYPE_INITIAL_DEPRESSION, STEP_TYPE_ROLLING, &
                                  STEP_TYPE_MOVE_BACK, STEP_TYPE_REAPPLY_LOAD, &
                                  STEP_TYPE_RELEASE_NODES]))) then
            write(*,"(A,I0,A)") 'Step type = ', step_type, ' not recognized'
            write(*,*) 'usub_utils_mod, get_step_type'
            call xit()
        endif
        
    end function

end module usub_utils_mod