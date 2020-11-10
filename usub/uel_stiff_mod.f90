module uel_stiff_mod
implicit none
    
    double precision, allocatable, save :: uel_stiffness(:,:)
    double precision, save              :: first_call_time
    
    contains
    
subroutine set_uel_time()
implicit none
    integer             :: time_values(8)
    
    call date_and_time(values=time_values)
    first_call_time = (time_values(5)*60 + time_values(6))*60 + time_values(7) + time_values(8)/1000.d0
    write(*,"(A,I02,A,I02,A,I02,A,I03)") 'SET UEL TIME: ', time_values(5), ':', time_values(6), ':', time_values(7), '.', time_values(8)

end subroutine

subroutine print_uel_time(pre_string)
implicit none
    character(len=*), optional  :: pre_string
    integer                     :: time_values(8)
    double precision            :: run_time
    
    call date_and_time(values=time_values)
    run_time = (time_values(5)*60 + time_values(6))*60 + time_values(7) + time_values(8)/1000.d0
    if (present(pre_string)) then
        write(*,"(A,F0.3)") pre_string, run_time - first_call_time
    else
        write(*,"(F0.3)") run_time - first_call_time
    endif
    
end subroutine
    
    
subroutine allocate_uel_stiffness(scale_factor)
use filenames_mod, only : uel_stiffness_file_name
use usub_utils_mod, only : get_fid
implicit none
    double precision, intent(in):: scale_factor 
    integer                     :: file_id          ! File identifier
    integer                     :: ndof             ! Number of dofs (read from file)
    integer                     :: i, j             ! Iterators
    double precision            :: tmp
   !integer                     :: check_i, check_j

    file_id = get_fid(uel_stiffness_file_name)
    
    ! The number of dofs is written on the first line as a single integer
    read(file_id, *) ndof
    
    ! Allocate the stiffness
    allocate(uel_stiffness(ndof, ndof))
    
    do i=1,ndof
        do j=i,ndof
            read(file_id, *) tmp
            uel_stiffness(i, j) = tmp*scale_factor
            uel_stiffness(j, i) = uel_stiffness(i, j)
            ! To check that current setup provides correct indices
            ! Requires to modify output from python scripts to include indices
            !read(file_id, *) check_i, check_j, tmp
            !if (i /= check_i) write(*, *) j, '/=', check_i, '(check i)'
            !if (j /= check_j) write(*, *) j, '/=', check_j, '(check j)'
            !uel_stiffness(i, j) = tmp
            !uel_stiffness(j, i) = tmp
        enddo
    enddo
    
end subroutine allocate_uel_stiffness
   
function get_ndof() result(ndof)
implicit none
    integer     :: ndof
    
    ndof = size(uel_stiffness,1)
    
end function

end module uel_stiff_mod