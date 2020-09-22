!DEC$ FREEFORM

module disp_mod
implicit none

contains

subroutine get_fid(base_name, file_id)
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

subroutine get_bc_value(cycle_nr, node, jdof, bc_val, node_type)
implicit none
    integer, intent(in)             :: cycle_nr     ! Cycle number for the previous rollover
    integer, intent(in)             :: node, jdof   ! Node and dof number
    double precision, intent(out)   :: bc_val       ! Value for boundary condition written in file
    integer, intent(out)            :: node_type    ! 1: Reference point node (rotation included)
                                                    ! 2: Contact node (only linear displacements)
    double precision                :: read_dbl(3)  ! Array to save info from bc file in
    integer                         :: read_node    ! Integer to save node number from bc file to
    character(len=100)              :: filename     ! Base file name (without path) for bc-file
    integer                         :: file_id      ! File identifier for bc-file written by urdfil
    integer                         :: io_status    ! I/O status
    
    write(filename, "(A, I0, A)") 'bc_step', cycle_nr, '.txt'
    call get_fid(filename, file_id)
    
    read(file_id, *) read_node, read_dbl
    if (read_node == node) then
        node_type = 1
        if (jdof==6) then
            bc_val = read_dbl(3)
        else
            bc_val = read_dbl(jdof)
        endif
    else    
        node_type = 2
        do while (read_node/=node)
            read(file_id, *) read_node, read_dbl(1:2)
        enddo
        bc_val = read_dbl(jdof)
    endif
    
    close(file_id)
    
end subroutine

subroutine get_rpar(cycle_nr, rtime, rlength, rangle)
implicit none
    character(len=*), parameter     :: RPAR_FILENAME = 'rolling_parameters.txt'
    integer, intent(in)             :: cycle_nr     ! The number of rollover cycles, starting at 1
    double precision, intent(out)   :: rtime        ! Rolling time
    double precision, intent(out)   :: rlength      ! Rolling length, i.e. u1 at end of rolling step
    double precision, intent(out)   :: rangle       ! Rolling angle, i.e. ur3 at end of rolling step
    integer                         :: io_status    ! I/O status key
    integer                         :: file_id      ! File identifier for RPAR_FILENAME
    character(len=256)              :: line_str     ! Line in RPAR_FILENAME
    double precision                :: line_dbl(4)  ! Line in RPAR_FILENAME converted to double
    
    call get_fid(RPAR_FILENAME, file_id)
    
    line_dbl = 0     ! To enter loop (first cycle should be 1)
    !write(*,*) 'cycle_nr = ', cycle_nr
    do while (int(line_dbl(1)+0.5) <= cycle_nr)  ! int() rounds towards 0, so adding 0.5 avoids float
                                                 ! to int conversion errors
        rtime = line_dbl(2)
        rlength = line_dbl(3)
        rangle = line_dbl(4)
        read(file_id, *, iostat=io_status) line_dbl
        ! Check if we are on an empty line or at the end of the file (allow up to 4 chars)
        if (io_status /= 0) then    ! End of file or line missing info (e.g. empty line)
            exit
        endif
        !write(*, "(I0, 3F10.5)") int(line_dbl(1)+0.5), line_dbl(2:4)
    enddo
    
    close(file_id)
    

end subroutine

subroutine get_bc_rolling(cycle_nr, time, jdof, bc_val)
implicit none
    integer, intent(in)             :: cycle_nr     ! The number of rollover cycles, starting at 1
    double precision, intent(in)    :: time(3)      ! Step, total, increment time
    integer, intent(in)             :: jdof         ! Degree of freedom 
    double precision, intent(out)   :: bc_val       ! Prescribed boundary condition value
    
    double precision                :: rtime        ! Rolling time
    double precision                :: rlength      ! Rolling length, i.e. u1 at end of rolling step
    double precision                :: rangle       ! Rolling angle, i.e. ur3 at end of rolling step
    
    call get_rpar(cycle_nr, rtime, rlength, rangle)
    if (jdof == 1) then     ! x-displacement
        bc_val = rlength*time(1)/rtime
    elseif (jdof == 6) then ! z-rotation
        bc_val = rangle*time(3)/rtime
    else
        write(*,"(A, I0, A)") 'jdof = ', jdof, ' should not be specified in rolling step'
        call xit()
    endif
    
end subroutine

subroutine get_bc_init_depression(time, jdof, bc_val)
implicit none
    double precision, intent(in)    :: time(3)      ! Step, total, increment time
    integer, intent(in)             :: jdof         ! Degree of freedom 
    double precision, intent(out)   :: bc_val       ! Prescribed boundary condition value
    double precision                :: ttime        ! Total time for initial depression step
    double precision                :: depr         ! Total value of u2 after initial depression
    integer                         :: file_id      ! File identifier to initial_depression file
    
    if (jdof /= 2) then ! x-displacement and z-rotation zero during initial depression
        bc_val = 0.0
    else
        call get_fid('initial_depression.txt', file_id)
        read(file_id,*) ttime, depr
        bc_val = depr*time(1)/ttime
    endif
    
end subroutine
    
end module

subroutine disp(u,kstep,kinc,time,node,noel,jdof,coords)
use disp_mod
implicit none
    integer, parameter  :: N_STEP_INITIAL = 2   ! Number of steps including first rollover
    integer, parameter  :: N_STEP_BETWEEN = 4   ! Number of steps between rollover simulations
    ! Interface variables for disp subroutine
    double precision    :: u(3)         ! u(1) is total value of dof (except rotation where the 
                                        ! incremental value should be specified). u(2:3) are the 
                                        ! du(1)/dt and d^2u(1)/dt^2 req. only in dyn. analyses. 
    double precision    :: time(3)      ! 1: current step time, 2: current total time, 
                                        ! 3: current time increment
    double precision    :: coords(3)    ! Current coordinates at end of previous increment if nlgeom
    integer             :: kstep, kinc  ! Step and increment number
    integer             :: node, noel   ! Node (not connector) and element number (not bc)
    integer             :: jdof         ! Degree of freedom number (at node) u(1) corresponds to.
    
    ! Internal variables
    integer             :: step_type    ! 1: return step, 2: reapply_step, 3: release nodes step
                                        ! 0: rolling_step_name    
    integer             :: cycle_nr     ! The number of rollover cycles, starting at 1
    integer             :: file_id      ! File identifier for bc-file written by urdfil
    integer             :: io_status    ! Status for file to handle i/o-errors
    integer             :: node_type    ! 1: Reference point, 2: Contact node
    double precision    :: bc_val       ! Value from bc file    
    
    step_type = mod(kstep-N_STEP_INITIAL, N_STEP_BETWEEN)
    cycle_nr = (kstep-step_type-N_STEP_INITIAL)/N_STEP_BETWEEN + 1
    if (kstep < 1) then             ! Should not occur
        return          
    elseif (kstep == 1) then        ! Initial depression
        call get_bc_init_depression(time, jdof, bc_val)
    elseif (step_type == 0) then    ! Rolling step (only called for reference point)
        cycle_nr = (kstep-N_STEP_INITIAL)/N_STEP_BETWEEN + 1
        call get_bc_rolling(cycle_nr, time, jdof, bc_val)
    else                            ! Move_back or re-application of load
        call get_bc_value(cycle_nr, node, jdof, bc_val, node_type)
        if ((step_type > 1).and.(node_type==1).and.(jdof==6)) then
            bc_val = 0.0  ! No change in wheel rotation
        endif
    endif
    u(1) = bc_val
    
    if (bc_val /= bc_val) then  ! Check for nan-values
        call xit()
    endif
        
end subroutine