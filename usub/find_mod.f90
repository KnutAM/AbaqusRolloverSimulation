module find_mod
implicit none

private

public  :: find                 ! Find position in an array being equal to a given value

interface find
    procedure find_int_1d, find_int_2d
end interface find


contains

function find_int_1d(array, val_to_find) result(ind)
implicit none
    integer, intent(in) :: array(:)
    integer, intent(in) :: val_to_find
    integer             :: ind, tmp_ind(1)
    
    tmp_ind = minloc(abs(array - val_to_find))
    ind = tmp_ind(1)
    
    if (abs(array(ind)-val_to_find) /= 0) ind = -1
    
    
end function find_int_1d
    
function find_int_2d(array, val_to_find) result(ind)
implicit none
    integer, intent(in) :: array(:,:)
    integer, intent(in) :: val_to_find
    integer             :: ind(2)
    
    ind = minloc(abs(array - val_to_find))
    
    if (abs(array(ind(1), ind(2))-val_to_find) /= 0) ind = -1
    
end function find_int_2d

end module