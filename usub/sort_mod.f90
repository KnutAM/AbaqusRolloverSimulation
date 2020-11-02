module sort_mod
use abaqus_utils_mod, only : xit    ! Use when testing outside abaqus, comment away otherwise
implicit none

private

public  :: sort                 ! Sort an array (int or double)
public  :: sortinds             ! Get indices that sorts an array (int or double)
public  :: unique               ! Get the unique elements of an array (double)

interface sort
    procedure sort_int, sort_dbl
end interface sort

interface sortinds
    procedure sortinds_int, sortinds_dbl
end interface sortinds

interface unique
    procedure unique_dbl
end interface unique

contains

! Sort array
subroutine sort_int(array)
implicit none
    integer, intent(inout)          :: array(:)     ! Array to be sorted
    
    integer, allocatable            :: tmp_array(:) ! Temporary internal storage
    logical, allocatable            :: unused(:)    ! Logical array to remove assigned values in 
                                                    ! minloc
    integer                         :: k1           ! Iterator
    integer                         :: min_ind(1)   ! Smallest index
    
    allocate(tmp_array, source=array)
    allocate(unused(size(array)))
    unused = .true.
    
    do k1=1,size(array)
        min_ind = minloc(tmp_array, mask=unused)
        array(k1) = tmp_array(min_ind(1))
        unused(min_ind) = .false.
    enddo
    
end subroutine sort_int

subroutine sort_dbl(array)
implicit none
    double precision, intent(inout) :: array(:)     ! Array to be sorted
    
    double precision, allocatable   :: tmp_array(:) ! Temporary internal storage
    logical, allocatable            :: unused(:)    ! Logical array to remove assigned values in 
                                                    ! minloc
    integer                         :: k1           ! Iterator
    integer                         :: min_ind(1)   ! Smallest index
    
    allocate(tmp_array, source=array)
    allocate(unused(size(array)))
    unused = .true.
    
    do k1=1,size(array)
        min_ind = minloc(tmp_array, mask=unused)
        array(k1) = tmp_array(min_ind(1))
        unused(min_ind) = .false.
    enddo
    
end subroutine sort_dbl

! Get sorting indices of array
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

! Get unique values in array
subroutine unique_dbl(full_vector, unique_vector, tolerance)
implicit none
    ! Note: full_vector will be sorted.
    ! Elements that are determined to be unique have maximum difference tolerance
    ! Default tolerance is 1.e-14*sum(abs(full_vector))/size(full_vector)
    double precision, intent(inout)             :: full_vector(:)
    double precision, allocatable, intent(out)  :: unique_vector(:)
    double precision, intent(in), optional      :: tolerance
    
    double precision, allocatable               :: unique_vec_tmp(:)
    double precision    :: tol  ! Internal variable for tolerance
    integer             :: kf   ! Iterator for full vector
    integer             :: kf0  ! Value of iterator for current unique set of values
    integer             :: ku   ! Iterator for unique vector
    
    if (present(tolerance)) then
        tol = tolerance
    else
        tol = 1.e-14*sum(abs(full_vector))/size(full_vector)
    endif
    
    allocate(unique_vec_tmp(size(full_vector)))
    
    call sort(full_vector)
    
    kf0 = 1
    ku = 1
    do kf=2,size(full_vector)
        if (full_vector(kf) > (full_vector(kf0) + tol)) then
            unique_vec_tmp(ku) = sum(full_vector(kf0:(kf-1)))/(kf-kf0)
            kf0 = kf
            ku = ku + 1
        endif
    enddo
    unique_vec_tmp(ku) = sum(full_vector(kf0:size(full_vector)))/(size(full_vector)-kf0 + 1)
    
    allocate(unique_vector(ku))
    unique_vector = unique_vec_tmp(1:ku)
    
end subroutine unique_dbl

end module