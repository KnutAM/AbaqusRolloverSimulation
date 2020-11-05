! Relies on
! - step_type_mod
! - load_param_mod
module disp_mod
implicit none
    
    private
    
    public      :: get_bc_rail_rp
    public      :: get_bc_wheel_rp
    public      :: get_bc_wheel_contact

contains

subroutine get_bc_rail_rp(step_type, cycle_nr, time, node_jdof, bc_val)
use step_type_mod, only: STEP_TYPE_ROLLING
use load_param_mod, only: get_rail_rolling_ext, get_rail_noroll_ext
implicit none
    integer, intent(in)                 :: step_type
    integer, intent(in)                 :: cycle_nr
    double precision, intent(in)        :: time(3)
    integer, intent(in)                 :: node_jdof
    double precision, intent(out)       :: bc_val
    
    double precision                    :: rext, rext_last
    
    if (node_jdof == 3) then    ! Apply rail extension
        if (step_type == STEP_TYPE_ROLLING) then
            bc_val = get_rail_rolling_ext(time_in_step=time(2))
        else
            bc_val = get_rail_noroll_ext()
        endif
    else        
        bc_val = 0.0
    endif
    
end subroutine get_bc_rail_rp

subroutine get_bc_wheel_rp(step_type, cycle_nr, time, node_jdof, bc_val)
use step_type_mod, only: STEP_TYPE_INITIAL_DEPRESSION, STEP_TYPE_ROLLING, STEP_TYPE_MOVE_BACK
use load_param_mod, only: is_load_param_read, read_load_param, get_rp_initial_depression_bc, &
                          get_rp_rolling_wheel_bc, get_rp_move_back_bc
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
        bc_val = get_rp_initial_depression_bc(node_jdof, time_in_step)
    elseif (step_type == STEP_TYPE_ROLLING) then
        bc_val = get_rp_rolling_wheel_bc(node_jdof, time)
    elseif (step_type == STEP_TYPE_MOVE_BACK) then
        bc_val = get_rp_move_back_bc(node_jdof)
    else
        write(*,*) 'bc for wheel rp requested for unsupported step type'
        write(*,"(A,I0)") 'step_type = ', step_type
    endif
    
    
end subroutine get_bc_wheel_rp

subroutine get_bc_wheel_contact(step_type, cycle_nr, node_label, node_jdof, bc_val)
use step_type_mod, only : STEP_TYPE_MOVE_BACK
use load_param_mod, only : get_contact_node_bc
implicit none
    integer, intent(in)                 :: step_type
    integer, intent(in)                 :: cycle_nr
    integer, intent(in)                 :: node_label
    integer, intent(in)                 :: node_jdof
    double precision, intent(out)       :: bc_val
    
    if (any(step_type == [STEP_TYPE_MOVE_BACK])) then
        bc_val = get_contact_node_bc(node_label, node_jdof)
    else
        write(*,*) 'Did not expect request for wheel contact node boundary conditions for'
        write(*,"(A,I0)") 'step of type, step_type = ', step_type
        call xit()
    endif
    
end subroutine get_bc_wheel_contact

end module

