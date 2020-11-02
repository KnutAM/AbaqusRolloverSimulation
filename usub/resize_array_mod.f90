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