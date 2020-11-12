module load_param_mod
use abaqus_utils_mod
implicit none
	
    private 
    
    ! Setup routines
    public  :: is_load_param_read       ! Check if load parameters have been read
    public  :: read_load_params         ! Initial setup to read in the load param at start of 
                                        ! simulation
    ! Update and get loading routines
    public  :: is_updated               ! Check if cycle is up to date
    public  :: update_cycle             ! Update the loading parameters, done each cycle
    public  :: get_rolling_par          ! 
    
    ! Wheel reference point motion
    public  :: set_rp_bc
    public  :: get_rp_initial_depression_bc
    public  :: get_rp_rolling_wheel_bc
    public  :: get_rp_move_back_bc
    
    ! Wheel contact nodes motion
    public  :: set_contact_node_bc
    public  :: get_contact_node_bc
    
    ! Rail reference point motion
    public  :: get_rail_rolling_ext
    public  :: get_rail_noroll_ext
    
    ! Static load parameters (not changed during simulation)
    double precision, save              :: rail_length
    double precision, save              :: initial_depression_speed
    integer, allocatable, save          :: update_cycles(:)
    double precision, allocatable, save :: rolling_times(:)
    double precision, allocatable, save :: rot_per_lengths(:)
    double precision, allocatable, save :: rail_extensions(:)
    
    ! Dynamic load parameters (may be updated each cycle)
    integer, save                       :: cycle_spec_ind = 1   ! Current position in update_cycle
    integer, save                       :: updated_cycle = -1   ! For which cycle the data is updated
    double precision, save              :: rolling_time         ! Current duration of rolling step
    double precision, save              :: rot_per_length       ! Current rotation per rolling length
    double precision, save              :: rail_extension_last=0! Rail extension for last cycle
    double precision, save              :: rail_extension=0     ! Current rail extension (dz)
    double precision, allocatable, save :: node_u_bc(:,:,:)     ! Displacements for nodes
    double precision, save              :: u_rp_bc_end_last(6)  ! wheel rp pos, end of last cycle
    double precision, save              :: u_rp_bc_start(6)     ! wheel rp pos, start of cur cycle
    double precision, save              :: u_rp_bc_end(6)       ! wheel rp pos, end of cur cycle
    
    contains
    
    ! Setup routines
    function is_load_param_read() result(is_read)
    implicit none
        logical     :: is_read
        
        is_read = allocated(update_cycles)
        
    end function is_load_param_read
    
    subroutine read_load_params()
    use filenames_mod, only: load_param_file_name
    use usub_utils_mod, only: get_fid, check_iostat
    implicit none
        integer             :: file_id
        integer             :: num_cycles_specified
        integer             :: k1
        integer             :: io_status
        character(len=256)  :: error_message
        
        file_id = get_fid(load_param_file_name)
        
        read(file_id,*, iostat=io_status) rail_length
        call check_iostat(io_status, 'Could not read rail length from "'//load_param_file_name//'"')
        read(file_id,*, iostat=io_status) initial_depression_speed
        call check_iostat(io_status, 'Could not read initial depression speed from "'//load_param_file_name//'"')
        read(file_id,*, iostat=io_status) num_cycles_specified
        call check_iostat(io_status, 'Could not read number of cycles from "'//load_param_file_name//'"')
        allocate(update_cycles(num_cycles_specified+1))
        allocate(rolling_times(num_cycles_specified))
        allocate(rot_per_lengths(num_cycles_specified))
        allocate(rail_extensions(num_cycles_specified))
        do k1=1,num_cycles_specified
            read(file_id,*, iostat=io_status) update_cycles(k1), rolling_times(k1), rot_per_lengths(k1), rail_extensions(k1)
            write(error_message, "(A,I0,A,I0,A)") 'Could not read info for cycle spec nr ', k1, &
                                 ', when given that ', num_cycles_specified, ' cycles are specified'
            call check_iostat(io_status, error_message)
        enddo
        ! Add extra element that ensures that we never will see this cycle
        update_cycles(num_cycles_specified+1) = huge(update_cycles(1))
        
        close(file_id)
        write(*,*) 'LOADING DATA READ'
        write(*,*) 'update_cycles: ', update_cycles
        write(*,*) 'rolling_times: ', rolling_times
        write(*,*) 'rot_per_lengths: ', rot_per_lengths
        write(*,*) 'rail_extensions: ', rail_extensions
        call update_cycle(0)
        call setup_initial_rolling_cycle()
        
    end subroutine
    
    subroutine setup_initial_rolling_cycle()
    implicit none
        u_rp_bc_start = 0.d0
        u_rp_bc_end = 0.d0
        u_rp_bc_end(3) = rail_length
        u_rp_bc_end(4) = rail_length*rot_per_lengths(1)
        
    end subroutine
    
    ! Update and get loading routines
    subroutine update_cycle(cycle_nr)
    implicit none
        integer, intent(in)     :: cycle_nr
        write(*,"(A,I0)") 'Updating to cycle nr: ', cycle_nr
        rail_extension_last = rail_extension
        if (cycle_nr == 0) then ! Initial depression
            cycle_spec_ind = 1
            rail_extension = 0.0
        elseif (cycle_nr == 1) then !First rolling cycle
            cycle_spec_ind = 1
            rolling_time = rolling_times(1)
            rot_per_length = rot_per_lengths(1)
            rail_extension = rail_extensions(1)
        elseif (cycle_nr >= update_cycles(cycle_spec_ind+1)) then
            ! Subsequent loading with new specification
            cycle_spec_ind = cycle_spec_ind + 1
            rolling_time = rolling_times(cycle_spec_ind)
            rot_per_length = rot_per_lengths(cycle_spec_ind)
            rail_extension = rail_extensions(cycle_spec_ind)
        endif
            
        write(*,"(A,I0)") 'cycle_spec_ind: ', cycle_spec_ind
        write(*,"(A,F0.3)") 'rolling_time: ', rolling_time
        write(*,"(A,F0.3)") 'rot_per_length: ', rot_per_length
        write(*,"(A,F0.3)") 'rail_extension: ', rail_extension
        updated_cycle = cycle_nr
    end subroutine

    function is_updated(cycle_nr)
    implicit none
        integer, intent(in)     :: cycle_nr
        logical                 :: is_updated
        
        is_updated = cycle_nr == updated_cycle
    end function
    
    subroutine get_rolling_par(the_rail_length, the_rot_per_length, the_rail_extension)
    implicit none
        double precision        :: the_rail_length
        double precision        :: the_rot_per_length
        double precision        :: the_rail_extension    
        
        the_rail_length = rail_length
        the_rot_per_length = rot_per_length
        the_rail_extension = rail_extension
        
    end subroutine
    
    ! Wheel reference point motion
    subroutine set_rp_bc(bc_end_last, bc_start, bc_end)
    implicit none
        double precision, intent(in)    :: bc_end_last(6)
        double precision, intent(in)    :: bc_start(6)
        double precision, intent(in)    :: bc_end(6)
        
        u_rp_bc_end_last = bc_end_last
        u_rp_bc_start = bc_start
        u_rp_bc_end = bc_end

    end subroutine
    
    function get_rp_initial_depression_bc(jdof, time_in_step) result(bc_val)
    implicit none
        integer, intent(in)             :: jdof
        double precision, intent(in)    :: time_in_step
        double precision                :: bc_val
        
        if (jdof==2) then
            bc_val = initial_depression_speed*time_in_step
        else
            bc_val = 0.d0
        endif
        
    end function
    
    function get_rp_rolling_wheel_bc(jdof, time) result(bc_val)
    implicit none
        integer, intent(in)             :: jdof
        double precision, intent(in)    :: time(3)
        double precision                :: bc_val
        
        double precision                :: time_in_step     ! time(2)
        double precision                :: time_increment   ! time(3)
        
        if (jdof <= 3) then ! Linear displacement, give value to go to
            time_in_step = time(2)
            bc_val = u_rp_bc_start(jdof) + (u_rp_bc_end(jdof)-u_rp_bc_start(jdof))*(time_in_step/rolling_time)
        elseif (jdof <=6) then  ! Rotation, give value increment
            time_increment = time(3)
            bc_val = (u_rp_bc_end(jdof)-u_rp_bc_start(jdof))*(time_increment/rolling_time)
        else
            write(*,*) 'load_param_mod:get_rp_rolling_wheel_bc: jdof > 6 not supported'
            call xit()
        endif
    
    end function
    
    function get_rp_move_back_bc(jdof) result(bc_val)
    implicit none
        integer, intent(in)             :: jdof
        double precision                :: bc_val
        
        if (jdof <= 3) then ! Linear displacement, give value to go to
            bc_val = u_rp_bc_start(jdof)
        elseif (jdof <=6) then  ! Rotation, give value increment
            bc_val = u_rp_bc_start(jdof)-u_rp_bc_end_last(jdof)
        else
            write(*,*) 'load_param_mod:get_rp_move_back_bc: jdof > 6 not supported'
            call xit()
        endif
    
    end function
    
    ! Wheel contact nodes motion
    subroutine set_contact_node_bc(mesh_inds, u_vals)
    use node_id_mod, only : get_mesh_size
    implicit none
        integer, intent(in)             :: mesh_inds(2) ! Indices from the get_inds function
        double precision, intent(in)    :: u_vals(3)    ! Values to set
        integer                         :: mesh_size(2)
        
        if (.not.allocated(node_u_bc)) then
            mesh_size = get_mesh_size()
            allocate(node_u_bc(3, mesh_size(1), mesh_size(2)))
        endif
        
        node_u_bc(:, mesh_inds(1), mesh_inds(2)) = u_vals
        
    end subroutine
    
    function get_contact_node_bc(label, jdof) result(bc_val)
    use node_id_mod, only : get_inds
    implicit none
        integer, intent(in)         :: label
        integer, intent(in)         :: jdof
        double precision            :: bc_val
        integer                     :: mesh_inds(2)
        
        mesh_inds = get_inds(label)
        bc_val = node_u_bc(jdof, mesh_inds(1), mesh_inds(2))
        
    end function
        
    ! Rail reference point motion
    function get_rail_rolling_ext(time_in_step) result(delta_z)
    implicit none
        double precision, intent(in)        :: time_in_step
        double precision                    :: delta_z
        
        delta_z = rail_extension_last + (rail_extension - rail_extension_last)*time_in_step/rolling_time
    
    end function
    
    function get_rail_noroll_ext() result (delta_z)
    implicit none
        double precision                    :: delta_z
        
        delta_z = rail_extension_last
    
    end function
    
        
end module load_param_mod