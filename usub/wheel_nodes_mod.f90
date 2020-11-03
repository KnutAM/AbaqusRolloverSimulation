! Module to organize the wheel contact nodes
module wheel_nodes_mod
implicit none
    
    ! Set at beginning of simulation, never changed
    integer, save                   :: rp_node_label
    integer, allocatable, save      :: node_label_matrix(:,:)
    double precision, save          :: angle_incr
    
    ! Initialized at beginning of simulation, changed values each cycle
    double precision, allocatable, save :: node_u_bc(:,:,:)
    double precision, save              :: rp_u_bc(6)
    
    
    contains

    subroutine setup_mesh_info(node_labels, node_coordinates)
    implicit none
        integer, intent(in)             :: node_labels(:)           ! size=(num_nodes)
        double precision, intent(in)    :: node_coordinates(:,:)    ! size=(3, num_nodes)
        
        double precision, allocatable   :: xcoords(:), uxcoords(:)
        double precision, allocatable   :: angles(:), uangles(:)
        double precision, allocatable   :: x_dist_square(:), a_dist_square(:)
        double precision                :: max_radius
        
        integer                         :: nt, na, nx   ! Number of nodes (total, angular, x)
        integer                         :: ka, kx       ! Iterators in angular and x directions
        integer                         :: min_ind(1)   ! Index of identified point
        
        nt = size(ndoe_labels)
        allocate(xcoords(nt), angles(nt))
        allocate(x_dist_square(nt), a_dist_square(nt))
        
        max_radius = sqrt(maxval(node_coordinates(2,:)^2 + node_coordinates(3, :)^2))
        
        angles = atan2(-node_coordinates(3,:), -node_coordinates(2, :))
        xcoords = node_coordinates(1,:)
        
        call unique(angles, uangles, TOL/max_radius)
        call unique(xcoords, uxcoords, TOL)
        
        na = size(uangles)
        nx = size(uxcoords)
        
        allocate(node_label_matrix(na, nx))
        
        do kx=1,nx
            x_dist_square = (uxcoords(kx) - xcoords)^2
            do ka=1,na
                a_dist_square = ((uangles(ka) - angles)*max_radius)^2
                min_ind = minloc(x_dist_square + a_dist_square)
                node_label_matrix(ka, kx) = node_labels(min_ind(1))
                if ((x_dist_square(min_ind(1))+a_dist_square(min_ind(1))) > 2*TOL^2) then
                    write(*,*) 'setup_mesh_inds could not find the point'
                    write(*,"(A,I0,A,I0)") 'kx = ', kx, ', ka = ', ka
                    call xit()
                endif
            enddo
        enddo
        
        angle_incr = (uangles(na) - uangles(1))/(na-1)
        
        allocate(node_u_bc(3, na, nx))
        
    end subroutine setup_mesh_info
    
    function get_inds(node_label) result(mesh_inds)
    implicit none
        integer, intent(in)     :: node_label
        integer                 :: mesh_inds(2)
        
        mesh_inds = maxloc(node_label_matrix == node_label)
        
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
    
    
end module wheel_nodes_mod
