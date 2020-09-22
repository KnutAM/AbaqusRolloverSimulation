!DEC$ FREEFORM
! Assume the following about the .fil results:
! 1) Only two node sets will have output. One is contact nodes and the other is the reference point.
!	 The order between these can be arbitrary and we cannot use the set names (seem not to match 
!	 with the specification in the input file, but are just numbers)
! 2) Write specific for 2-dimensional analysis. Hence, if 3 displacements we know rotation is 
!	 included and the current set if for the reference point. If 2 datapoints, it is for contact 
!	 nodes


module resize_array_mod
implicit none

private

public  :: expand_array         ! Expand an allocatable array by specifying the increase in size
public  :: contract_array       ! Contract an allocatable array by specifying the new size    

interface expand_array
    procedure expand_array_1d_int, &
              expand_array_1d_dbl, &
              expand_array_2d_int, &
              expand_array_2d_dbl
end interface expand_array

interface contract_array
    procedure contract_array_1d_int, &
              contract_array_1d_dbl, &
              contract_array_2d_int, &
              contract_array_2d_dbl
end interface

contains


! Expand 1d integer array
subroutine expand_array_1d_int(array, expand_amount)
implicit none
    integer, allocatable            ::  array(:)        ! Array to be expanded
    integer                         ::  expand_amount   ! Amount to expand array with
    integer, allocatable            ::  tmp(:)          ! Temporary storage while expanding array
    integer                         ::  s               ! size(array)
    integer                         ::  ns              ! New size (s+expand_amount)
    
    s = size(array)
    ns = s + expand_amount
    allocate(tmp, source=array)
    deallocate(array)
    allocate(array(ns))
    array(1:s) = tmp
    
end subroutine


! Expand 1d dbl array
subroutine expand_array_1d_dbl(array, expand_amount)
implicit none
    double precision, allocatable   ::  array(:)        ! Array to be expanded
    integer                         ::  expand_amount   ! Amount to expand array with
    double precision, allocatable   ::  tmp(:)          ! Temporary storage while expanding array
    integer                         ::  s               ! size(array)
    integer                         ::  ns              ! New size (s+expand_amount)
    
    s = size(array)
    ns = s + expand_amount
    allocate(tmp, source=array)
    deallocate(array)
    allocate(array(ns))
    array(1:s) = tmp
    
end subroutine


! Expand 2d int array
subroutine expand_array_2d_int(array, expand_amount)
implicit none
    integer, allocatable            ::  array(:,:)      ! Array to be expanded
    integer                         ::  expand_amount(2)! Amount to expand array with
    integer, allocatable            ::  tmp(:,:)        ! Temporary storage while expanding array
    integer                         ::  s(2)            ! size(array)
    integer                         ::  ns(2)           ! New size (s+expand_amount)
    
    s = size(array)
    allocate(tmp, source=array)
    deallocate(array)
    allocate(array(ns(1), ns(2)))
    array(1:s(1),1:s(2)) = tmp
    
end subroutine


! Expand 2d dbl array
subroutine expand_array_2d_dbl(array, expand_amount)
implicit none
    double precision, allocatable   ::  array(:,:)      ! Array to be expanded
    integer                         ::  expand_amount(2)! Amount to expand array with
    double precision, allocatable   ::  tmp(:,:)        ! Temporary storage while expanding array
    integer                         ::  s(2)            ! size(array)
    integer                         ::  ns(2)           ! New size (s+expand_amount)
    
    s = size(array)
    allocate(tmp, source=array)
    deallocate(array)
    allocate(array(ns(1), ns(2)))
    array(1:s(1),1:s(2)) = tmp
    
end subroutine


! Contract 1d integer array
subroutine contract_array_1d_int(array, new_size)
implicit none
    integer, allocatable            ::  array(:)    ! Array to be expanded
    integer                         ::  new_size    ! Size of new array (only elems up to this)
    integer, allocatable            ::  tmp(:)      ! Temporary storage while expanding array
    
    allocate(tmp, source=array)
    deallocate(array)
    allocate(array(new_size))
    array = tmp(1:new_size)
    
end subroutine

! Contract 1d double array
subroutine contract_array_1d_dbl(array, new_size)
implicit none
    double precision, allocatable   ::  array(:)    ! Array to be expanded
    integer                         ::  new_size    ! Size of new array (only elems up to this)
    double precision, allocatable   ::  tmp(:)      ! Temporary storage while expanding array
    
    allocate(tmp, source=array)
    deallocate(array)
    allocate(array(new_size))
    array = tmp(1:new_size)
    
end subroutine

! Contract 2d integer array
subroutine contract_array_2d_int(array, new_size)
implicit none
    integer, allocatable            ::  array(:,:)  ! Array to be expanded
    integer                         ::  new_size(2) ! Size of new array (only elems up to this)
    integer, allocatable            ::  tmp(:,:)    ! Temporary storage while expanding array
    
    allocate(tmp, source=array)
    deallocate(array)
    allocate(array(new_size(1), new_size(2)))
    array = tmp(1:new_size(1), 1:new_size(2))
    
end subroutine

! Contract 2d double array
subroutine contract_array_2d_dbl(array, new_size)
implicit none
    double precision, allocatable   ::  array(:,:)  ! Array to be expanded
    integer                         ::  new_size(2) ! Size of new array (only elems up to this)
    double precision, allocatable   ::  tmp(:,:)    ! Temporary storage while expanding array
    
    allocate(tmp, source=array)
    deallocate(array)
    allocate(array(new_size(1), new_size(2)))
    array = tmp(1:new_size(1), 1:new_size(2))
    
end subroutine

end module

module sortinds_mod
implicit none

private

public  :: sortinds             ! Determine indices that sorts the given array

interface sortinds
    procedure sortinds_int, sortinds_dbl
end interface sortinds

contains

subroutine sortinds_dbl(array, sort_inds)
! Crude subroutine to determine sort_inds such that array(sort_inds) is sorted in ascending order
implicit none
    double precision        :: array(:)     ! Array with values to be sorted
    integer, allocatable    :: sort_inds(:) ! Index array to be created
    logical, allocatable    :: unused(:)    ! Logical array to remove assigned values in minloc
    integer                 :: k1           ! Iterator
    
    allocate(unused(size(array)))
    
    if (.not.allocated(sort_inds)) then
        allocate(sort_inds(size(array)))
    else
        if (size(sort_inds).ne.size(array)) then
            write(*,*) 'array and sort_inds must have same size in sortinds subroutine'
            call xit()
        endif
    endif
        
    unused = .true.
        
    do k1=1,size(array)
        sort_inds(k1) = minloc(array, dim=1, mask=unused)
        unused(sort_inds(k1)) = .false.
    enddo
    
end subroutine

subroutine sortinds_int(array, sort_inds)
! Crude subroutine to determine sort_inds such that array(sort_inds) is sorted in ascending order
implicit none
    integer                 :: array(:)     ! Array with values to be sorted
    integer, allocatable    :: sort_inds(:) ! Index array to be created
    logical, allocatable    :: unused(:)    ! Logical array to remove assigned values in minloc
    integer                 :: k1           ! Iterator
    
    allocate(unused(size(array)))
    
    if (.not.allocated(sort_inds)) then
        allocate(sort_inds(size(array)))
    else
        if (size(sort_inds).ne.size(array)) then
            write(*,*) 'array and sort_inds must have same size in sortinds subroutine'
            call xit()
        endif
    endif
        
    unused = .true.
        
    do k1=1,size(array)
        sort_inds(k1) = minloc(array, dim=1, mask=unused)
        unused(sort_inds(k1)) = .false.
    enddo
    
end subroutine

end module
    
module urdfil_mod
use resize_array_mod
use sortinds_mod
implicit none
    integer, parameter  :: NPRECD = 2           ! Precision for floats
    integer, parameter  :: GUESS_NUM = 100     ! Guess for number of contact nodes
    contains
    

subroutine get_node_data(node_n, node_val, array)
implicit none
    ! Input/output
    integer, allocatable            :: node_n(:)        ! Contact node numbers [Nc]
    double precision, allocatable   :: node_val(:,:)    ! Contact node displacements [num_values,Nc]
    double precision, intent(inout) :: array(:)         ! Array to which .fil info is saved
    
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
        node_val(1:num_values,k1) = array(4:(3+num_values))
        
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

module bc_mod
implicit none
    
contains

subroutine set_bc(node_n, node_u, node_c, rp_n, rp_u, angle_incr, cycle_nr)
implicit none
    integer, intent(in)             :: node_n(:)    ! Node numbers
    double precision, intent(in)    :: node_u(:,:)  ! Node displacements
    double precision, intent(in)    :: node_c(:,:)  ! Node coordinates
    integer, intent(in)             :: rp_n         ! Node number for reference point
    double precision, intent(in)    :: rp_u(:)      ! Reference point disp (incl. rot. at pos 3)
    double precision, intent(in)    :: angle_incr   ! Angular nodal spacing
    integer, intent(in)             :: cycle_nr     ! Current rollover cycle
    
    integer                         :: nnod             ! Number of nodes
    
    integer                         :: num_elem_roll    ! How many elements to roll back
    double precision                :: roll_back_angle  ! What angle to roll to return back
    double precision                :: return_angle     ! What angle to return back to
    
    integer                         :: old_ind  ! Node indices for the old node from which the disp
    integer                         :: new_ind  ! should be applied to the new node
    
    double precision                :: dx_rp(2)         ! Linear motion of reference point
    double precision                :: x0_new(2)        ! Initial position of new node
    double precision                :: x_old(2)         ! Current position of corresponding old node
    double precision                :: x_new(2)         ! New (cf. current) position of new node
    double precision                :: u_new(2)         ! Displacements applied to new nodes
    double precision                :: u_new_rp(2)      ! Disp applied to ref. point
    
    integer                         :: cwd_length   ! Required when calling abaqus getoutdir
    character(len=256)              :: filename     ! Full path to file with boundary conditions
    integer                         :: file_id      ! File identifier for boundary condition file    
    integer                         :: io_status    ! Input/output status
    
    ! Open output file
    call getoutdir(filename, cwd_length)
    
    ! Check that cwd is not too long (current limit of 256 from abaqus getoutdir)
    if (len(trim(filename)) > (len(filename)-20)) then
        write(*,*) 'ERROR: Current working directory path too long'
        write(*,*) 'cwd = '//trim(filename)
        call xit()
    endif
    
    ! Create filename
    write(filename, "(A, A, I0, A)") trim(filename), '/bc_step', cycle_nr, '.txt'
    
    open(newunit=file_id, file=trim(filename), iostat=io_status)
    
    ! Calculate motion for the reference point
    num_elem_roll = nint(rp_u(3)/angle_incr)
    roll_back_angle = - num_elem_roll*angle_incr
    return_angle = rp_u(3) + roll_back_angle
    
    ! Equations that help understanding why we arrive at dx_rp and that being used later (Eq. 4)
    !x_rp_old = (rp_c - rp_u) + rp_u                (1)
    !x_rp_new = (rp_c - rp_u) + [0.0, rp_u(2)]      (2)
    !dx_rp = x_rp_new - x_rp_old                    (3)
    dx_rp = [-rp_u(1), 0.d0]
    
    ! Save reference point prescribed displacements to first row. Rotation is the incremental value
    u_new_rp = [0.d0, rp_u(2)]
    write(file_id, "(I0, 3ES25.15)", iostat=io_status) rp_n, u_new_rp(1), u_new_rp(2), roll_back_angle
    
    ! Save remaining node prescribed displacements to subsequent rows
    nnod = size(node_n)
    do old_ind=1,(nnod-num_elem_roll)
        new_ind = old_ind + num_elem_roll
        x0_new = node_c(:, new_ind) - node_u(:, new_ind)
        x_old = node_c(:, old_ind)
        
        !x_new = x_rp_new + (x_old - x_rp_old) = x_old + dx_rp  (4)
        x_new = x_old + dx_rp
        u_new = x_new - x0_new
        write(file_id, "(I0, 2ES25.15)") node_n(new_ind), u_new(1), u_new(2)
    enddo
    
    close(file_id)
    
end subroutine
    
end module bc_mod

subroutine urdfil(lstop,lovrwrt,kstep,kinc,dtime,time)
use urdfil_mod
use bc_mod
implicit none
    integer, parameter  :: N_STEP_INITIAL = 2   ! Number of steps including first rollover
    integer, parameter  :: N_STEP_BETWEEN = 4   ! Number of steps between rollover simulations
    ! Variables to be defined
    integer             :: lstop        ! Flag, set to 1 to stop analysis
    integer             :: lovrwrt      ! Flag, set to 1 to allow overwriting of
                                        ! results from current increment by next
    double precision    :: dtime        ! Time increment, can be updated
    ! Variables passed for information
    integer             :: kstep, kinc  ! Current step and increment, respectively
    double precision    :: time(2)      ! Time at end of increment (step, total)
    
    ! Internal variables
    integer, allocatable            :: node_n(:)            ! Contact node numbers
    double precision, allocatable   :: node_u(:,:)          ! Contact node displacements
    double precision, allocatable   :: node_c(:,:)          ! Contact node coordinates
    integer                         :: rp_n                 ! Reference point node number
    double precision                :: rp_u(3)              ! Reference point displacements
    double precision                :: angle_incr           ! Angular nodal spacing (wheel)
    integer                         :: cycle_nr             ! Rollover cycle nr
    
    if (mod(kstep-N_STEP_INITIAL, N_STEP_BETWEEN) == 0) then
        cycle_nr = (kstep-N_STEP_INITIAL)/N_STEP_BETWEEN + 1
        call get_data(node_n, node_u, node_c, rp_n, rp_u, angle_incr, kstep, kinc)
        call set_bc(node_n, node_u, node_c, rp_n, rp_u, angle_incr, cycle_nr)
    endif
    
    lstop = 0   ! Continue analysis (set lstop=1 to stop analysis)
    lovrwrt = 1 ! Overwrite read results. (These results not needed later, set to 0 to keep in .fil)
    
end subroutine