module disp_mod
implicit none
    
    private
    
    public      :: get_bc_rail_rp
    public      :: get_bc_wheel_rp
    public      :: get_bc_wheel_contact

contains

subroutine get_bc_rail_rp(step_type, cycle_nr, time, node_jdof, bc_val)
implicit none
    integer, intent(in)                 :: step_type
    integer, intent(in)                 :: cycle_nr
    double precision, intent(in)        :: time(3)
    integer, intent(in)                 :: node_jdof
    double precision, intent(out)       :: bc_val
    
    ! To get started, this is not supported and we always return 0.0
    bc_val = 0.0
    
end subroutine get_bc_rail_rp

subroutine get_bc_wheel_rp(step_type, cycle_nr, time, node_jdof, bc_val)
use load_param_mod, only: is_load_param_read, read_load_param, get_initial_depression_bc
implicit none
    integer, intent(in)                 :: step_type
    integer, intent(in)                 :: cycle_nr
    double precision, intent(in)        :: time(3)
    integer, intent(in)                 :: node_jdof
    double precision, intent(out)       :: bc_val
    
    double precision                    :: time_in_step
    
    time_in_step = time(2)
    if (step_type == STEP_TYPE_INITIAL_DEPRESSION) then
        ! This step type will occur first, so we will read load params here the first time
        if (.not.is_load_param_read()) then
            call read_load_param()
        endif
        bc_val = get_initial_depression_bc(node_jdof, time_in_step)
    elseif (step_type == STEP_TYPE_ROLLING)
        bc_val = get_rolling_wheel_rp(node_jdof, time)
    elseif (step_type == STEP_TYPE_MOVE_BACK)
        bc_val = get_move_back_rp(node_jdof)
    else
        write(*,*) 'bc for wheel rp requested for unsupported step type'
        write(*,"(A,I0)") 'step_type = ', step_type
    endif
    
    
end subroutine get_bc_wheel_rp

subroutine get_bc_wheel_contact(step_type, cycle_nr, node_label, node_jdof, bc_val)
implicit none
    integer, intent(in)                 :: step_type
    integer, intent(in)                 :: cycle_nr
    integer, intent(in)                 :: node_label
    integer, intent(in)                 :: node_jdof
    double precision, intent(out)       :: bc_val
    
    integer                             :: mesh_inds(2)
    
    if (any(step_type == [STEP_TYPE_MOVE_BACK])) then
        mesh_inds = get_mesh_inds(node_label)
        bc_val = get_u_bc_val(mesh_inds, node_jdof)
    else
        write(*,*) 'Did not expect request for wheel contact node boundary conditions for'
        write(*,"(A,I0)") 'step of type, step_type = ', step_type
        call xit()
    endif
    
end subroutine get_bc_wheel_contact



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
    
    write(filename, "(A, I0, A)") 'bc_cycle', cycle_nr, '.txt'
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
            read(file_id, *, iostat=io_status) read_node, read_dbl(1:2)
            if (io_status /= 0) then
                write(*,"(A,I0,A,I0,A)") 'disp cannot find node nr ', node, ' in bc_step', cycle_nr, '.txt'
                call xit()
            endif
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

