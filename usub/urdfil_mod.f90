! Relies on the following modules
! - abaqus_utils_mod
! - node_id_mod
! - sort_mod
module urdfil_mod
use abaqus_utils_mod
implicit none
    
    private
    
    public  :: get_data_first_time  ! Use first time urdfil is called to setup node_id_mod
    public  :: get_data             ! Use for subsequent calls, requires only displacements to be
                                    ! written to result file

    integer, parameter  :: GUESS_NUM = 100  ! Guess for number of contact nodes
    
    ! Abaqus .fil file record keys
    ! General keys
    integer, parameter  :: FIL_INCREMENT_START = 2000       ! Written at start of increment with output requests
    integer, parameter  :: FIL_INCREMENT_END = 2001         ! Written at end of increment with output requests
    integer, parameter  :: FIL_OUTPUT_REQUEST_DEF = 1911    ! Written for each output request
    ! Node output keys
    integer, parameter  :: FIL_NODE_DISP = 101  ! Node displacements, attributes = [Node num, u1, u2, ...]
    integer, parameter  :: FIL_NODE_COORD = 107 ! Node (deformed) coordinates, attr = [Node num, x1, x2, ...]
    
    contains

function get_record_length(array) result (record_length)
implicit none
    double precision, intent(in)    :: array(:)
    integer                         :: record_length
    
    record_length = transfer(array(1), 1)
end function

function get_record_type(array) result (record_type)
implicit none
    double precision, intent(in)    :: array(:)
    integer                         :: record_type
    
    record_type = transfer(array(2), 1)
    
end function

subroutine get_node_data(node_n, node_val, array)
! Subroutine to node data for multiple nodes. The array input/output variable should on input 
! contain the values for the first node. The record type (e.g. 101 => node displacements) of this 
! entry is read and saved as the reference record type. Records are read for as long as the record
! type remains equal to the reference, and the end of file is not encountered. 
! Typically, to initiate this subroutine the caller would make a call to Abaqus dbfile, resulting 
! in the array to pass to the present subroutine. The record type can be obtained as 
! transfer(array(2), 1)
! On exit, array 
use resize_array_mod, only : expand_array, contract_array
implicit none
    ! Input/output
    integer, allocatable, intent(out)           :: node_n(:)        ! Node numbers [Nc]
    double precision, allocatable, intent(out)  :: node_val(:,:)    ! Node values [num_values,Nc]
    double precision, intent(inout)             :: array(:)         ! Array to which .fil info is saved
    
    ! Internal variables
    integer                         :: fil_status       ! Status for .fil file input/output
    integer                         :: record_type_ref  ! The record type key that should be read
                                                        ! (should remain constant, stop reading when
                                                        !  the record type key changes)
    integer                         :: record_type      ! The current entry's record type key
    integer                         :: num_values       ! Number of values per node
    integer                         :: k1               ! Counter
    
    k1 = 0
    fil_status = 0
    num_values = get_record_length(array) - 3
    record_type_ref = get_record_type(array)
    record_type = record_type_ref
    allocate(node_n(GUESS_NUM), node_val(num_values,GUESS_NUM))
    
    do while ((fil_status==0).and.(record_type==record_type_ref))
        if (k1 >= size(node_n)) then
            call expand_array(node_n, GUESS_NUM)
            call expand_array(node_val, [0, GUESS_NUM])
        endif
        
        k1 = k1 + 1
        node_n(k1) = transfer(array(3), 1)
        node_val(:,k1) = array(4:(3+num_values))
        
        call dbfile(0, array, fil_status)
        record_type = get_record_type(array)
    enddo
    
    ! Resize arrays to match number of nodes
    call contract_array(node_n, k1)
    call contract_array(node_val, [num_values, k1])
    
    
end subroutine
   
subroutine get_data_first_time(kstep, kinc, contact_node_disp, wheel_rp_disp, rail_rp_disp)
! Read node coordinates, displacements and labels and send to node_id_mod
! Return the contact_node_displacements, and rp disp/rot for wheel/rail
use node_id_mod, only : setup_mesh_info, is_wheel_rp_node, is_rail_rp_node
use sort_mod, only : sortinds
implicit none
    integer, intent(in)                             :: kstep    ! Step number
    integer, intent(in)                             :: kinc     ! Increment number
    double precision, allocatable, intent(out)      :: contact_node_disp(:,:,:)
    double precision, allocatable, intent(out)      :: wheel_rp_disp(:)
    double precision, allocatable, intent(out)      :: rail_rp_disp(:)
    
    ! Variables for reading .fil files
    double precision                :: array(513)       ! Array to save float information to
    integer                         :: fil_status       ! Status for .fil file input/output
    integer                         :: record_length    ! Variable describing current record length
    integer                         :: record_type_key  ! Variable describing current record type
    
    ! Temporary variables for node data
    double precision, allocatable   :: node_disp(:,:)   ! Nodal displacements
    integer, allocatable            :: node_labels_d(:) ! Node labels from nodal disps
    double precision, allocatable   :: node_coords(:,:) ! Nodal coordinates
    integer, allocatable            :: node_labels_c(:) ! Node labels from nodal coords
    integer, allocatable            :: sort_inds(:)     ! Indices to sort labels to ensure compatibility
    
    ! Set position to current increment and step
    call posfil(kstep,kinc,array,fil_status)
    
    do while (fil_status==0)
        record_type_key = get_record_type(array)
        if (record_type_key == FIL_OUTPUT_REQUEST_DEF) then  ! New output request
            call dbfile(0, array, fil_status)
            record_type_key = get_record_type(array)
            do while (.not.any(record_type_key == [FIL_OUTPUT_REQUEST_DEF, FIL_INCREMENT_END]))
                if (record_type_key == FIL_NODE_COORD) then
                    call get_node_data(node_labels_c, node_coords, array)
                elseif (record_type_key == FIL_NODE_DISP) then
                    call get_node_data(node_labels_d, node_disp, array)
                else
                    call dbfile(0, array, fil_status)
                endif
                record_type_key = get_record_type(array)
            enddo
            ! Need to determine which nodes we have data for
            if (size(node_labels_d) > 1) then   ! Contact nodes
                ! Check that node_coords and node_disp have the same order of nodes
                if (.not.all(node_labels_c == node_labels_d)) then
                    call sortinds(node_labels_d, sort_inds)
                    node_labels_d = node_labels_d(sort_inds)
                    node_disp = node_disp(:, sort_inds)
                    call sortinds(node_labels_c, sort_inds)
                    ! We do not need node_cn anymore, from now on equal to node_labels_d.
                    ! node_labels_c = node_labels_c(sort_inds)  
                    node_coords = node_coords(:, sort_inds)
                endif
                ! When we have the same order, the initial nodal positions can be calculated
                node_coords = node_coords - node_disp
                call setup_mesh_info(node_labels_d, node_coords)
                call get_contact_node_disp(node_labels_d, node_disp, contact_node_disp)
            else    ! Reference point node
                if (is_wheel_rp_node(node_labels_d(1))) then
                    allocate(wheel_rp_disp(size(node_disp, 1)))
                    wheel_rp_disp = node_disp(:,1)
                elseif (is_rail_rp_node(node_labels_d(1))) then
                    allocate(rail_rp_disp(size(node_disp, 1)))
                    rail_rp_disp = node_disp(:,1)
                else
                    write(*,*) 'WARNING: Could not determine node type for URDFIL'
                endif
            endif
            
            if (allocated(node_labels_c)) deallocate(node_labels_c)
            if (allocated(node_labels_d)) deallocate(node_labels_d)
            if (allocated(node_coords)) deallocate(node_coords)
            if (allocated(node_disp)) deallocate(node_disp)
            
        else
            call dbfile(0, array, fil_status)
        endif
    enddo
    
end subroutine

subroutine get_data(kstep, kinc, contact_node_disp, wheel_rp_disp, rail_rp_disp)
! Return the contact_node_displacements, and rp disp/rot for wheel/rail
use node_id_mod, only : is_wheel_rp_node, is_rail_rp_node
implicit none
    integer, intent(in)                             :: kstep    ! Step number
    integer, intent(in)                             :: kinc     ! Increment number
    double precision, allocatable, intent(out)      :: contact_node_disp(:,:,:)
    double precision, allocatable, intent(out)      :: wheel_rp_disp(:)
    double precision, allocatable, intent(out)      :: rail_rp_disp(:)
    
    ! Variables for reading .fil files
    double precision                :: array(513)       ! Array to save float information to
    integer                         :: fil_status       ! Status for .fil file input/output
    integer                         :: record_length    ! Variable describing current record length
    integer                         :: record_type_key  ! Variable describing current record type
    
    ! Temporary variables for node data
    double precision, allocatable   :: node_disp(:,:)   ! Nodal displacements
    integer, allocatable            :: node_labels(:)   ! Node labels
    
    ! Set position to current increment and step
    call posfil(kstep,kinc,array,fil_status)
    
    do while (fil_status==0)
        record_length = get_record_length(array)
        record_type_key = get_record_type(array)
        if (record_type_key == FIL_NODE_DISP) then  ! Displacement output request
            call get_node_data(node_labels, node_disp, array)
            ! Need to determine which nodes we have data for
            if (size(node_labels) > 1) then   ! Contact nodes
                call get_contact_node_disp(node_labels, node_disp, contact_node_disp)
            else    ! Reference point node
                if (is_wheel_rp_node(node_labels(1))) then
                    allocate(wheel_rp_disp(size(node_disp, 1)))
                    wheel_rp_disp = node_disp(:,1)
                elseif (is_rail_rp_node(node_labels(1))) then
                    allocate(rail_rp_disp(size(node_disp, 1)))
                    rail_rp_disp = node_disp(:,1)
                else
                    write(*,*) 'WARNING: Could not determine node type for URDFIL'
                endif
            endif
            if (allocated(node_labels)) deallocate(node_labels)
            if (allocated(node_disp)) deallocate(node_disp)
        else
            call dbfile(0, array, fil_status)
        endif
    enddo
    
end subroutine

subroutine get_contact_node_disp(node_labels, node_disp, contact_node_disp)
use node_id_mod, only : get_inds, get_mesh_size
implicit none
    integer, intent(in)                         :: node_labels(:)
    double precision, intent(in)                :: node_disp(:,:)
    double precision, allocatable, intent(out)  :: contact_node_disp(:,:,:)
    
    integer                                     :: mesh_size(2)
    integer                                     :: mesh_inds(2)
    integer                                     :: k1
    
    mesh_size = get_mesh_size()
    allocate(contact_node_disp(size(node_disp,1), mesh_size(1), mesh_size(2)))
    
    do k1=1,size(node_labels)
        mesh_inds = get_inds(node_labels(k1))
        contact_node_disp(:, mesh_inds(1), mesh_inds(2)) = node_disp(:, k1)
    enddo
    
end subroutine

end module urdfil_mod
