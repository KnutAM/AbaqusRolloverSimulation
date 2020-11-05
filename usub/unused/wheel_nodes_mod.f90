! Module to organize the wheel contact nodes
module wheel_nodes_mod
implicit none

    private
    
    public  :: is_mesh_info_setup   ! Logical function to check if mesh info has been setup
    public  :: setup_mesh_info      ! Subroutine to setup the mesh info
    public  :: get_inds             ! Function to get mesh_inds from node_label
    public  :: update_cycle         ! Subroutine to set the cycle number for the bc values provided
    public  :: check_cycle          ! Function to check that bc values are updated
    public  :: set_u_bc_vals        ! Subroutine to set bc to contact nodes from mesh_inds
    public  :: get_u_bc_val         ! Function to get bc for contact nodes from mesh_inds and jdof
    public  :: set_u_rp_bc          ! Subroutine to set bc for rp node
    public  :: get_u_rp_val_start   ! Function to get rp position at start of cycle
    public  :: get_u_rp_val_end     ! Function to get rp position at end of cycle
    public  :: get_du_rp_val_start  ! Function to get change of rp pos from end of last to start of 
                                    ! current cycle
    public  :: get_du_rp_val_end    ! Function to get change of rp pos during current cycle
    
    ! Set at beginning of simulation, never changed

    
    contains
    
  
    subroutine update_cycle(cycle_nr)
    implicit none
        integer     :: cycle_nr
        
        updated_cycle = cycle_nr
    end subroutine
    
    function check_cycle(cycle_nr) result(is_updated)
    implicit none
        logical     :: is_updated
        
        is_updated = cycle_nr == updated_cycle
    end function
    
    subroutine set_u_bc_val(mesh_inds, jdof, bc_val)
    implicit none
        integer, intent(in)             :: mesh_inds(2) ! Indices from the get_inds function
        integer, intent(in)             :: jdof         ! Degree of freedom <= 3
        double precision, intent(in)    :: bc_val       ! Value to set
        
        node_u_bc(jdof, mesh_inds(1), mesh_inds(2)) = bc_val
        
    end subroutine set_u_bc_val
    
    subroutine set_u_bc_vals(mesh_inds, bc_vals)
    implicit none
        integer, intent(in)             :: mesh_inds(2) ! Indices from the get_inds function
        double precision, intent(in)    :: bc_vals(3)   ! Values to set
        
        node_u_bc(:, mesh_inds(1), mesh_inds(2)) = bc_vals
        
    end subroutine set_u_bc_vals
    
    function get_u_bc_val(mesh_inds, jdof) result(bc_val)
    implicit none
        integer, intent(in)             :: mesh_inds(2) ! Indices from the get_inds function
        integer, intent(in)             :: jdof         ! Degree of freedom <= 3
        double precision                :: bc_val       ! Value to get
        
        bc_val = node_u_bc(jdof, mesh_inds(1), mesh_inds(2))
        
    end function
    
    function get_u_bc_vals(mesh_inds) result(bc_vals)
    implicit none
        integer, intent(in)             :: mesh_inds(2) ! Indices from the get_inds function
        double precision                :: bc_vals(3)   ! Values to get
        
        bc_vals = node_u_bc(:, mesh_inds(1), mesh_inds(2))
        
    end function
    
    subroutine set_u_rp_bc(bc_end_last, bc_start, bc_end)
    implicit none
        double precision, intent(in)    :: bc_end_last(6)
        double precision, intent(in)    :: bc_start(6)
        double precision, intent(in)    :: bc_end(6)
        
        u_rp_bc_end_last = bc_end_last
        u_rp_bc_start = bc_start
        u_rp_bc_end = bc_end

    end subroutine
    
    function get_u_rp_val_start(jdof) result(bc_val)
    implicit none
        integer, intent(in)     :: jdof
        double precision        :: bc_val
        
        bc_val = u_rp_bc_start(jdof)
        
    end function get_u_rp_val_start
    
    function get_u_rp_val_end(jdof) result(bc_val)
    implicit none
        integer, intent(in)     :: jdof
        double precision        :: bc_val
        
        bc_val = u_rp_bc_end(jdof)
    
    end function get_u_rp_val_end
    
    function get_du_rp_val_start(jdof) result(dbc_val)
    implicit none
        integer, intent(in)     :: jdof
        double precision        :: dbc_val
    
        dbc_val = u_rp_bc_start(jdof) - u_rp_bc_end_last(jdof)
    
    end function get_du_rp_val_start
    
    function get_du_rp_val_end(jdof) result(dbc_val)
    implicit none
        integer, intent(in)     :: jdof
        double precision        :: dbc_val
        
        dbc_val = u_rp_bc_end(jdof) - u_rp_bc_start(jdof)
        
    end function get_du_rp_val_end
    
end module wheel_nodes_mod
