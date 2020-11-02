! Module to organize the wheel contact nodes
module wheel_nodes_mod
implicit none
    
    integer, allocatable, save      :: mesh_inds(:,:)
    
    contains

    subroutine setup_mesh_inds(node_labels, node_coordinates)
    implicit none
        integer, intent(in)             :: node_labels(:)
        double precision, intent(in)    :: node_coordinates(:,:)
        
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
        
        allocate(mesh_inds(na, nx))
        
        do kx=1,nx
            x_dist_square = (uxcoords(kx) - xcoords)^2
            do ka=1,na
                a_dist_square = ((uangles(ka) - angles)*max_radius)^2
                min_ind = minloc(x_dist_square + a_dist_square)
                mesh_inds(ka, kx) = node_labels(min_ind(1))
                if ((x_dist_square(min_ind(1))+a_dist_square(min_ind(1))) > 2*TOL^2) then
                    write(*,*) 'setup_mesh_inds could not find the point'
                    write(*,"(A,I0,A,I0)") 'kx = ', kx, ', ka = ', ka
                    call xit()
                endif
            enddo
        enddo
        
    end subroutine setup_mesh_inds
        
end module wheel_nodes_mod