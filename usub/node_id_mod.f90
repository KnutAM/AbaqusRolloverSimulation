! Module to identify which type of node we have and other info about nodes

module node_id_mod
use abaqus_utils_mod
implicit none

    private
    
    ! Information about status
    public  :: are_uel_coords_obtained
    public  :: is_mesh_info_setup
    
    ! External setup requests
    public  :: set_uel_coords
    public  :: setup_mesh_info          ! subroutine(node_labels, node_coordinates)
    
    ! Get node wheel node information
    public  :: get_inds                 ! function(node_label) result(mesh_inds)
    public  :: get_label                ! function(mesh_inds) result(node_label)
    public  :: get_node_coords          ! function(mesh_inds) result(node_coords)
    public  :: get_node_dofs            ! function(mesh_inds) result(node_dofs)
    public  :: get_mesh_size            ! function() result(size(wheel_contact_node_labels))
    public  :: get_angle_incr           ! function() result(the_angle_incr)
    public  :: get_element_order        ! function() result(the_element_order)
    
    ! Node type
    public  :: is_wheel_rp_node         ! function(node_label) result (is_wheel_rp)
    public  :: is_rail_rp_node          ! function(node_label) result (is_rail_rp)
    public  :: get_node_type_by_label   ! function(node_label) result(node_type)
    public  :: get_node_type            ! subroutine(node_label, node_coords, node_type)
    
    ! Constants
    public  :: NODE_TYPE_UNKNOWN        !
    public  :: NODE_TYPE_WHEEL_RP       !
    public  :: NODE_TYPE_RAIL_RP        !
    public  :: NODE_TYPE_WHEEL_CONTACT  !
    
    ! Parameters for node types
    integer, parameter  :: NODE_TYPE_UNKNOWN = -1
    integer, parameter  :: NODE_TYPE_WHEEL_RP = 1
    integer, parameter  :: NODE_TYPE_RAIL_RP = 2
    integer, parameter  :: NODE_TYPE_WHEEL_CONTACT = 3
    
    ! Internal parameters
    double precision, parameter         :: POS_TOL = 1.e-2
    
    ! Temporary storage until used, then deallocated
    double precision, allocatable, save :: uel_coords(:,:)
    
    ! Set at beginning of simulation, never changed
    logical, save                       :: uel_coords_obtained = .false.
    double precision, allocatable, save :: wheel_rp_coords(:)
    double precision, allocatable, save :: rail_rp_coords(:)
    integer, allocatable, save          :: wheel_rp_node_label
    integer, allocatable, save          :: rail_rp_node_label
    integer, allocatable, save          :: wheel_contact_node_labels(:,:)
    double precision, allocatable, save :: wheel_contact_node_coords(:,:,:)
    integer, allocatable, save          :: wheel_contact_node_dofs(:,:,:)
    integer, save                       :: element_order=0
    double precision, save              :: angle_incr=0
    
    
    contains
    
    function are_uel_coords_obtained() result(is_obtained)
    implicit none
        logical         :: is_obtained
        
        is_obtained = uel_coords_obtained
        
    end function
    
    subroutine set_uel_coords(the_uel_coords)
    implicit none
        double precision, intent(in)        :: the_uel_coords(:,:)
        
        allocate(uel_coords, source=the_uel_coords)
        uel_coords_obtained = .true.
        
    end subroutine
    
    function is_mesh_info_setup() result(is_setup)
    implicit none
        logical     :: is_setup
        
        is_setup = allocated(wheel_contact_node_labels)
        
    end function
    
    function get_mesh_size() result(mesh_size)
    implicit none
        integer     :: mesh_size(2)
        
        mesh_size = [size(wheel_contact_node_labels,1), size(wheel_contact_node_labels,2)]
        
    end function
    
    subroutine setup_mesh_info(node_labels, node_coordinates)
    use sort_mod, only : unique
    use usub_utils_mod, only : get_fid
    implicit none
        integer, intent(in)             :: node_labels(:)           ! size=(num_nodes)
        double precision, intent(in)    :: node_coordinates(:,:)    ! size=(3, num_nodes)
        
        double precision, allocatable   :: rel_coords(:,:)
        double precision, allocatable   :: xcoords(:), uxcoords(:)
        double precision, allocatable   :: angles(:), uangles(:)
        double precision, allocatable   :: x_dist_square(:), a_dist_square(:)
        double precision                :: max_radius
        
        integer                         :: nt, na, nx   ! Number of nodes (total, angular, x)
        integer                         :: ka, kx       ! Iterators in angular and x directions
        integer                         :: min_ind(1)   ! Index of identified point
        integer                         :: n_filled     ! Number of filled positions    
        
        ! Calculate coordinates relative the wheel center
        allocate(rel_coords, source=node_coordinates)
        if (.not.allocated(wheel_rp_coords)) then
            write(*,*) 'wheel rp coords should have been allocated by now, exiting...'
            call xit()
        endif
        do ka=1,3
            rel_coords(ka,:) = rel_coords(ka,:) - wheel_rp_coords(ka)
        enddo
        
        nt = size(node_labels)
        allocate(xcoords(nt), angles(nt))
        allocate(x_dist_square(nt), a_dist_square(nt))
        
        max_radius = sqrt(maxval(rel_coords(2,:)**2 + rel_coords(3, :)**2))
        
        angles = atan2(-rel_coords(3,:), -rel_coords(2, :))
        xcoords = rel_coords(1,:)
        
        call unique(angles, uangles, POS_TOL/max_radius)
        call unique(xcoords, uxcoords, POS_TOL)
        na = size(uangles)
        nx = size(uxcoords)
        
        allocate(wheel_contact_node_labels(na, nx))
        allocate(wheel_contact_node_coords(3, na, nx))
        wheel_contact_node_labels = -1
        wheel_contact_node_coords = 0.d0
        do kx=1,nx
            x_dist_square = (uxcoords(kx) - xcoords)**2
            do ka=1,na
                a_dist_square = ((uangles(ka) - angles)*max_radius)**2
                min_ind = minloc(x_dist_square + a_dist_square)
                if ((x_dist_square(min_ind(1))+a_dist_square(min_ind(1))) < 2*POS_TOL**2) then                    
                    wheel_contact_node_labels(ka, kx) = node_labels(min_ind(1))
                    wheel_contact_node_coords(:, ka, kx) = node_coordinates(:, min_ind(1))
                endif
            enddo
        enddo
        n_filled = na*nx - (-sum(wheel_contact_node_labels, mask=(wheel_contact_node_labels==-1)))
        if (n_filled == na*nx) then
            element_order = 1
        elseif (n_filled == nt) then
            element_order = 2
        else
            write(*,*) 'Could not find all node positions.'
            write(*,*) n_filled, nt, na, nx
            write(*,*) 'Identified positions (kx along rows, ka along cols):'
            write(*,"(10X)", advance="no")
            do kx=1,nx
                write(*, "(I5)", advance="no") kx
            enddo
            write(*,*) ''
            do ka=1,na
                write(*, "(I10)", advance="no") ka
                do kx=1,nx
                    write(*, "(I5)", advance="no") wheel_contact_node_labels(ka, kx)
                enddo
                write(*,*) ''
            enddo
        endif
        angle_incr = element_order*(uangles(na) - uangles(1))/(na-1)
        ! Allocate here as we have na and nx defined
        allocate(wheel_contact_node_dofs(3, na, nx))
        call get_wheel_contact_node_dofs()
        
    end subroutine setup_mesh_info
    
    subroutine get_wheel_contact_node_dofs()
    use find_mod, only: find
    implicit none
        integer             :: nnod
        integer             :: k1, mesh_inds(2)
        
        nnod = size(uel_coords,2)
        ! First 3 dofs are wheel rp translations
        ! Next 3 dofs are wheel rp rotations
        ! Thereafter comes wheel contact node translation dofs in pairs of 3 for each node
        ! First coords are wheel rp coordinates
        ! Thereafter comes wheel contact node coordinates, in same order as dofs
        do k1=2,nnod
            mesh_inds = find(wheel_contact_node_coords, uel_coords(:,k1), point_dim=1, tol=POS_TOL)
            wheel_contact_node_dofs(:, mesh_inds(1), mesh_inds(2)) = [1, 2, 3] + 3*k1
        enddo
        
        ! From now on we no longer need the uel_coords
        deallocate(uel_coords)
        
    end subroutine get_wheel_contact_node_dofs
    
    function get_angle_incr() result(the_angle_incr)
    implicit none
        double precision        :: the_angle_incr
        
        the_angle_incr = angle_incr
        
    end function
    
    function get_element_order() result(the_element_order)
    implicit none
        integer                 :: the_element_order
        
        the_element_order = element_order
        
    end function
    
    function get_inds(node_label) result(mesh_inds)
    use find_mod, only : find
    implicit none
        integer, intent(in)     :: node_label
        integer                 :: mesh_inds(2)
        
        mesh_inds = find(wheel_contact_node_labels, node_label)
        
    end function
    
    function get_label(mesh_inds) result(node_label)
    implicit none
        integer, intent(in)     :: mesh_inds(2)
        integer                 :: node_label
            
        node_label = wheel_contact_node_labels(mesh_inds(1), mesh_inds(2))
        
    end function
    
    function get_node_coords(mesh_inds) result(node_coords)
    implicit none
        integer, intent(in)     :: mesh_inds(2)
        double precision        :: node_coords(3)

        node_coords = wheel_contact_node_coords(:, mesh_inds(1), mesh_inds(2))
    end function
    
    function get_node_dofs(mesh_inds) result(node_dofs)
    implicit none
        integer, intent(in)     :: mesh_inds(2)
        integer                 :: node_dofs(3)

        node_dofs = wheel_contact_node_dofs(:, mesh_inds(1), mesh_inds(2))
    end function
    
    function is_wheel_rp_node(node_label) result(is_wheel_rp)
    implicit none
        integer, intent(in)             :: node_label
        logical                         :: is_wheel_rp
        
        if (allocated(wheel_rp_node_label)) then
            is_wheel_rp = node_label == wheel_rp_node_label
        else
            write(*,*) 'WARNING: is_wheel_rp_node called before wheel_rp_node_label has been set'
            is_wheel_rp = .false.
        endif
    end function
    
    function is_rail_rp_node(node_label) result(is_rail_rp)
    implicit none
        integer, intent(in)             :: node_label
        logical                         :: is_rail_rp
        
        if (allocated(rail_rp_node_label)) then
            is_rail_rp = node_label == rail_rp_node_label
        else
            write(*,*) 'WARNING: is_rail_rp_node called before rail_rp_node_label has been set'
            is_rail_rp = .false.
        endif
    end function
    
    subroutine get_node_type(node_label, node_coords, node_type)
    implicit none
        integer, intent(in)             :: node_label
        double precision, intent(in)    :: node_coords(3)
        integer, intent(out)            :: node_type
        
        ! Try first to get by label, this is the fastest method
        node_type = get_node_type_by_label(node_label)
        
        if (node_type == NODE_TYPE_UNKNOWN) then
            ! If node type not known, probably because label is not setup yet.
            ! Get rp node by coordinate will also setup the label
            call get_rp_node_type_by_coord(node_label, node_coords, node_type)
            if (node_type == NODE_TYPE_UNKNOWN) then
                write(*,*) 'Could not identify node type'
                if (.not.is_mesh_info_setup()) then
                    write(*,*) 'mesh info not setup, this is a likely cause'
                endif
                call xit()
            endif
        endif
    
    end subroutine
    
    subroutine get_rp_node_type_by_coord(node_label, node_coords, node_type)
    use linalg_mod, only : norm
    implicit none
        integer, intent(in)             :: node_label
        double precision, intent(in)    :: node_coords(3)
        integer, intent(out)            :: node_type
        
        if (.not.allocated(wheel_rp_coords)) then
            call set_rp_node_coords()
        endif
        
        if (norm(node_coords - wheel_rp_coords) < POS_TOL) then
            allocate(wheel_rp_node_label)
            wheel_rp_node_label = node_label
            node_type = NODE_TYPE_WHEEL_RP
        elseif (norm(node_coords - rail_rp_coords) < POS_TOL) then
            allocate(rail_rp_node_label)
            rail_rp_node_label = node_label
            node_type = NODE_TYPE_RAIL_RP
        else
            node_type = NODE_TYPE_UNKNOWN
        endif
        
    end subroutine
    
    function get_node_type_by_label(node_label) result(node_type)
    implicit none
        integer, intent(in)     :: node_label
        integer                 :: node_type
        
        node_type = NODE_TYPE_UNKNOWN
        
        if (allocated(wheel_rp_node_label)) then
            if (node_label == wheel_rp_node_label) then
                node_type = NODE_TYPE_WHEEL_RP
                return
            endif
        endif
        
        if (allocated(rail_rp_node_label)) then
            if (node_label == rail_rp_node_label) then
                node_type = NODE_TYPE_RAIL_RP
                return
            endif
        endif
        
        if (is_mesh_info_setup()) then
            if (all(get_inds(node_label) > -1)) then
                node_type = NODE_TYPE_WHEEL_CONTACT
                return
            endif
        endif
        
    end function get_node_type_by_label
        
    subroutine set_rp_node_coords()
    use filenames_mod, only : rp_node_coords_file_name
    use usub_utils_mod, only : get_fid, check_iostat
    implicit none
        integer             :: file_id
        integer             :: io_stat
        
        file_id = get_fid(rp_node_coords_file_name)
        allocate(wheel_rp_coords(3), rail_rp_coords(3))
        read(file_id, *, iostat=io_stat) wheel_rp_coords
        call check_iostat(io_stat, 'Could not read wheel_rp_coords from "'//rp_node_coords_file_name//'"')
        read(file_id, *, iostat=io_stat) rail_rp_coords
        call check_iostat(io_stat, 'Could not read rail_rp_coords from "'//rp_node_coords_file_name//'"')
        
    end subroutine
    
end module node_id_mod