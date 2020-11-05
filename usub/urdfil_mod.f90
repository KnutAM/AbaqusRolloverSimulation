
! Assume the following about the .fil results:
! 1) Only two node sets will have output. One is contact nodes and the other is the reference point.
!	 The order between these can be arbitrary and we cannot use the set names (seem not to match 
!	 with the specification in the input file, but are just numbers)
! 2) Write specific for 2-dimensional analysis. Hence, if 3 displacements we know rotation is 
!	 included and the current set if for the reference point. If 2 datapoints, it is for contact 
!	 nodes

module urdfil_mod
use resize_array_mod, only : expand_array, contract_array
implicit none
    integer, parameter  :: GUESS_NUM = 100  ! Guess for number of contact nodes
    contains
    

subroutine get_node_data(node_n, node_val, array)
! Subroutine to node data for multiple nodes. The array input/output variable should on input 
! contain the values for the first node. The record type (e.g. 101 => node displacements) of this 
! entry is read and saved as the reference record type. Records are read for as long as the record
! type remains equal to the reference, and the end of file is not encountered. 
! Typically, to initiate this subroutine the caller would make a call to Abaqus dbfile, resulting 
! in the array to pass to the present subroutine. The record type can be obtained as 
! transfer(array(2), 1)
! On exit, array 
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
    num_values = transfer(array(1), 1) - 3
    record_type_ref = transfer(array(2), 1)
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
        record_type = transfer(array(2), 1)
    enddo
    
    ! Resize arrays to match number of nodes
    call contract_array(node_n, k1)
    call contract_array(node_val, [num_values, k1])
    
    
end subroutine
    

subroutine get_data(node_n, node_u, node_c, rp_n, rp_u, angle_incr, kstep, kinc)
implicit none
    ! Output
    integer, allocatable            :: node_n(:)        ! Contact node numbers (disp) [Nc]
    double precision, allocatable   :: node_u(:,:)      ! Contact node displacements [2,Nc]
    double precision, allocatable   :: node_c(:,:)      ! Contact node coordinates [2,Nc]
    integer, intent(out)            :: rp_n             ! Reference point node number
    double precision, intent(out)   :: rp_u(3)          ! Reference point displacements
    double precision, intent(out)   :: angle_incr       ! Angular nodal spacing (wheel)
    
    ! Input
    integer, intent(in)             :: kstep, kinc      ! Current step and increment, resp.
    
    ! Variables for reading .fil files
    double precision                :: array(513)       ! Array to save float information to
    integer                         :: fil_status       ! Status for .fil file input/output
    integer                         :: record_length    ! Variable describing current record length
    integer                         :: record_type_key  ! Variable describing current record type
    
    ! Other internal variables
    integer, allocatable            :: tmp_n(:)         ! Temporary variable for getting node nums
    double precision, allocatable   :: tmp_c(:,:)       ! Temporary variable for getting node coords
    integer, allocatable            :: node_cn(:)       ! Contact node numbers (coord) [Nc]
    double precision                :: rp_c(2)          ! Reference point coordinates [2]
    
    ! Check that multiple data sources doesn't exist (for arrays that do not give alloc error)
    integer                         :: check_rp_disp
    integer                         :: check_rp_coord
    
    check_rp_disp = 0   
    check_rp_coord = 0
    ! Set position to current increment and step
    call posfil(kstep,kinc,array,fil_status)

    do while (fil_status==0)
        record_length = transfer(array(1), 1)
        record_type_key = transfer(array(2), 1)
        if (record_type_key==101) then  ! Node displacement information
            if ((record_length-3)==2) then      ! 2 displacements => contact node
                call get_node_data(node_n, node_u, array)
            elseif ((record_length-3)==3) then    ! 3 displacements => assume reference point
                rp_u = array(4:6)
                check_rp_disp = check_rp_disp + 1
            endif
        elseif (record_type_key==107) then  ! Node coordinates
            call get_node_data(tmp_n, tmp_c, array)
            if (size(tmp_n) > 1) then   ! More than one node, contact nodes
                allocate(node_cn, source=tmp_n)
                allocate(node_c, source=tmp_c)
            else
                rp_c = tmp_c(:,1)
                rp_n = tmp_n(1)
                check_rp_coord = check_rp_coord + 1
            endif
            deallocate(tmp_n, tmp_c)
        endif
        
        call dbfile(0, array, fil_status)
    enddo
    
    ! ERROR checking. Note that multiple node_u or node_c will lead to allocation error.
    if (.not.allocated(node_u)) then
        write(*,*) 'ERROR: Did not find node displacement data in .fil file'
        call xit()
    elseif (.not.allocated(node_c)) then
        write(*,*) 'ERROR: Did not find node coordinate data in .fil file'
        call xit()
    elseif (check_rp_disp /= 1) then
        write(*,"(A,I0,A)") 'ERROR: Found ', check_rp_disp, ' entries that could represent rp disp'
        call xit()
    elseif(check_rp_coord /= 1) then
        write(*,"(A,I0,A)") 'ERROR: Found ', check_rp_coord, ' entries that could represent rp coord'
        call xit()
    endif
    
    call sort_node_disp(rp_c, rp_u, node_cn, node_c, node_n, node_u, angle_incr)
    
end subroutine 

subroutine sort_node_disp(rp_c, rp_u, node_cn, node_c, node_n, node_u, angle_incr)
implicit none
    ! Sort node_n, node_u and node_c by angle to -y axis. 
    ! Also, calculate the angle increment between nodes
    double precision, intent(in)    :: rp_c(:)                      ! Reference point coordinates
    double precision, intent(in)    :: rp_u(3)                      ! Reference point displacements    
    integer, intent(in)             :: node_cn(:)                   ! Node numbers for coord
    integer, intent(inout)          :: node_n(:)                    ! Node numbers for disp
    double precision, intent(inout) :: node_c(:,:), node_u(:,:)     ! Node coords and disps
    double precision, intent(out)   :: angle_incr                   ! Angular nodal spacing (wheel)
    double precision, allocatable   :: angles(:)                    ! Node angles to -y axis
    double precision, allocatable   :: node_c_rel(:,:)              ! Node coords relative refpoint
    integer, allocatable            :: sort_inds(:)                 ! Sorting inds to sort
    integer                         :: n_nodes                      ! Number of nodes
    integer                         :: k1                           ! Iterator
    
    n_nodes = size(node_n)
    
    ! Step 1: Ensure that lists with coordinates and displacements have the same node order. 
    !         Probably, this is not necessary as the same node order is used each time, but if not 
    !         it will result in an error that is very hard to find. It is quick to compare anyways
    if (.not.all(node_cn == node_n)) then
        call sortinds(node_n, sort_inds)
        node_n = node_n(sort_inds)
        node_u = node_u(:, sort_inds)
        call sortinds(node_cn, sort_inds)
        ! node_cn = node_cn(sort_inds)  ! We do not need node_cn anymore, from now on equal to node_n.
        node_c = node_c(:, sort_inds)
    endif
    
    ! Step 2: Calculate coordinates relative reference point. 
    ! Note that with nlgeom=true coord are current coordinates, and we need the initial values.
    allocate(node_c_rel, source=node_c)
    do k1=1,n_nodes
        node_c_rel(:,k1) = (node_c(:,k1) - node_u(:,k1)) - (rp_c - rp_u(1:2))
    enddo
    
    ! Step 3: Calculate angles relative -y axis
    allocate(angles(n_nodes))
    angles = atan2(node_c_rel(1,:), -node_c_rel(2,:))
    
    ! HERE WE NEED TO SORT BOTH IN ANGLE DIRECTION AND X-DIRECTION. WOULD PROBABLY BE GOOD TO DO 
    ! THIS ONCE IN THE BEGINNING TO GET THE CORRECT NODE INDICES. THEN WE CAN KNOW HOW THE node_n 
    ! SHOULD BE, AND THE node_c AND node_u CAN FOLLOW. SEE PYTHON IMPLEMENTATION FOR HOW SUCH 
    ! ORGANIZATION CAN BE ACCOMPLISHED. 
    
    ! Get sorting indices based on angles
    call sortinds(angles, sort_inds)
    
    ! Sort node numbers, coordinates and displacements.
    node_n = node_n(sort_inds)
    node_c = node_c(:, sort_inds)
    node_u = node_u(:, sort_inds)
    
    ! Calculate angle increment:
    angle_incr = angles(sort_inds(2)) - angles(sort_inds(1))
    
end subroutine
 
end module urdfil_mod
