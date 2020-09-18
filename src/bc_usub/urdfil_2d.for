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
    
module urdfil_mod
use resize_array_mod
implicit none
    integer, parameter  :: NPRECD = 2           ! Precision for floats
    integer, parameter  :: GUESS_NUM = 100     ! Guess for number of contact nodes
    contains
    

subroutine get_node_data(node_n, node_val, array)
implicit none
    ! Input/output
    integer, allocatable            :: node_n(:)        ! Contact node numbers [Nc]
    double precision, allocatable   :: node_val(:,:)    ! Contact node displacements [num_values,Nc]
    double precision, intent(inout) :: array(513)       ! Array to which .fil info is saved
    
    ! Internal variables
    integer                         :: fil_status       ! Status for .fil file input/output
    integer                         :: record_type_key  ! Variable describing current record type
    integer                         :: num_values       ! Number of values per node
    integer                         :: k1               ! Counter
    
    k1 = 0
    fil_status = 0
    num_values = transfer(array(1), 1) - 3
    record_type_key = transfer(array(2), 1)
    allocate(node_n(GUESS_NUM), node_val(num_values,GUESS_NUM))
    
    do while ((fil_status==0).and.(record_type_key==101))
        if (k1 >= size(node_n)) then
            call expand_array(node_n, GUESS_NUM)
            call expand_array(node_val, [0, GUESS_NUM])
        endif
        
        k1 = k1 + 1
        node_n(k1) = transfer(array(3), 1)
        node_val(1:num_values,k1) = array(4:(3+num_values))
        
        call dbfile(0, array, fil_status)
        record_type_key = transfer(array(2), 1)
    enddo
    
    ! Resize arrays to match number of nodes
    write(*,*) 'Contracting arrays'
    call contract_array(node_n, k1)
    call contract_array(node_val, [num_values, k1])
    write(*,*) 'Done contracting arrays'
    
end subroutine
    

subroutine get_data(node_n, node_u, rp_u, kstep, kinc)
implicit none
    ! Output
    integer, allocatable            :: node_n(:)    ! Contact node numbers (disp) [Nc]
    double precision, allocatable   :: node_u(:,:)  ! Contact node displacements [2,Nc]
    double precision                :: rp_u(3)      ! Reference point displacements
    
    ! Input
    integer                         :: kstep, kinc              ! Current step and increment, resp.
    
    ! Variables for reading .fil files
    double precision                :: array(513)       ! Array to save float information to
    integer                         :: fil_status       ! Status for .fil file input/output
    integer                         :: record_length    ! Variable describing current record length
    integer                         :: record_type_key  ! Variable describing current record type
    
    ! Other internal variables
    integer, allocatable            :: node_cn(:)           ! Contact node numbers (coord) [Nc]
    double precision, allocatable   :: node_c(:,:)          ! Contact node coordinates [2,Nc]
    
    ! Check to ensure that multiple data sources does not exist
    integer                         :: check_rp_node_num_data       
    
    
    check_rp_node_num_data = 0
    
    ! Set position to current increment and step
    call posfil(kstep,kinc,array,fil_status)

    do while (fil_status==0)
        record_length = transfer(array(1), 1)
        record_type_key = transfer(array(2), 1)
        if (record_type_key==101) then  ! Node displacement information
            if ((record_length-3)==2) then      ! 2 displacements => contact node
                call get_node_data(node_n, node_u, array)
            elseif ((record_length-3)==3) then    ! 3 displacements => assume reference point
                rp_displacements = array(4:6)
                check_rp_node_num_data = check_rp_node_num_data + 1     ! Others will give allocation error
            endif
        elseif (record_type_key==107) then  ! Node coordinates
            call get_node_data(node_cn, node_c, array)
        endif
        
        call dbfile(0, array, fil_status)
    enddo
    
    if (check_rp_node_num_data > 1) then
        write(*,*) 'ERROR: multiple data sources found in .fil file'
        write(*,"(A,I1)") 'check_rp_node_num_data = ', check_rp_node_num_data
        call xit()  ! Quit analysis
    endif
    
    call sort_node_disp(node_cn, node_c, node_n, node_u)
    
end subroutine 

subroutine sort_node_disp(node_cn, node_c, node_n, node_u)
implicit none
    integer                         :: node_cn(:), node_n(:)        ! Node numbers (coord,disp)
    double precision                :: node_c(:,:), node_u(:,:)     ! Node coords and disps
    double precision, allocatable   :: angles(:)                    ! Node angles to -y axis
    integer, allocatable            :: sort_inds(:)                 ! Sorting inds to sort
    
    ! Sort node_n and node_u by angle. This ensures consistent numbering when applying boundary 
    ! conditions. To do this, we should also output the reference point coordinate. However, this 
    ! require some additional logic to separate from nodal information. Could use temporary variable 
    ! to save it in, and check if more than one node is in the set. (This should be done in get_data)
    
end subroutine
 
end module urdfil_mod

subroutine urdfil(lstop,lovrwrt,kstep,kinc,dtime,time)
use urdfil_mod
implicit none
    ! Variables to be defined
    integer             :: lstop        ! Flag, set to 1 to stop analysis
    integer             :: lovrwrt      ! Flag, set to 1 to allow overwriting of
                                        ! results from current increment by next
    double precision    :: dtime        ! Time increment, can be updated
    ! Variables passed for information
    integer             :: kstep, kinc  ! Current step and increment, respectively
    double precision    :: time(2)      ! Time at end of increment (step, total)
    
    ! New variables
    double precision, allocatable   :: node_u(:,:)          ! Contact node displacements
    integer, allocatable            :: node_n(:)            ! Contact node numbers
    double precision                :: rp_u(3)              ! Reference point displacements
    integer                         :: file_id, cwd_length
    CHARACTER(len=255)              :: cwd, filename        !
    integer                         :: k1                   ! Iterator
    
    
    
    call get_data(node_u, rp_u, kstep, kinc)
    
    ! Use Abaqus utility routine, getoutdir, to get the output directory of the current job
    ! Otherwise, a special temporary folder will contain all the files making it difficult to debug.
    call getoutdir(cwd, cwd_length)
    write(filename, "(A, I0, A)") '/fil_results_step', kstep, '.txt'
    file_id = 101
    
    open(file_id, file=trim(cwd)//trim(filename))
    write(*,*) 'urdfil called, writing to file'
    write(*,*) '"'//trim(cwd)//trim(filename)//'"'
    write(file_id,"(A4, A25, A25)") 'NUM', 'U1', 'U2'
    
    do k1=1,size(node_n)
        write(file_id,"(I4, E25.15, E25.15)") node_n(k1), node_u(1,k1), node_u(2,k1)
    enddo
    close(file_id)
    
    lstop = 0   ! Continue analysis (set lstop=1 to stop analysis)
    lovrwrt = 1 ! Overwrite read results. (These results not needed later, set to 0 to keep in .fil)
    
END