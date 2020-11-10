! Module for transforming user element for rotations
module uel_trans_mod
use abaqus_utils_mod
implicit none

    private

    public :: get_phi       !function(u) result(phi_rp)
    public :: get_u_prim    !subroutine(coords, u, u_prim)
    public :: get_f_glob    !subroutine(phi_rp, f_prim, f_glob)
    public :: get_k_glob    !subroutine(phi_rp, k_glob)

    contains
    
    function get_phi(u) result(phi_rp)
    implicit none
        double precision, intent(in)    :: u(:)
        double precision                :: phi_rp(3)
        
        phi_rp = u(4:6)
        
    end function get_phi

    subroutine get_u_prim(coords, u, u_prim)
    implicit none
        double precision, intent(in)    :: coords(:,:)      ! Node coordinates(dim, nodenr)
        double precision, intent(in)    :: u(:)             ! Displacements in global coordinates 
                                                            ! (rotated)
        double precision, intent(inout) :: u_prim(:)        ! Displacements in unrotated (initial) 
                                                            ! coordinates
        
        integer                         :: num_nodes        ! Number of nodes
        integer                         :: i1, i2, k1       ! Iterators
        double precision                :: rot_mat_t(3,3)   ! Transpose rotation matrix
        double precision                :: xi_minus_x0(3)   ! Vector from current wheel center to 
                                                            ! current node position
        
        num_nodes = (size(u)-3)/3
        
        rot_mat_t = transpose(get_rotation_matrix(get_phi(u)))
        
        u_prim(1:6) = 0.0
        
        do k1=2,num_nodes
            i1 = 3*k1 + 1
            i2 = i1 + 2
            xi_minus_x0 = coords(:, k1) + u(i1:i2) - (coords(:, 1) + u(1:3))
            u_prim(i1:i2) = matmul(rot_mat_t, xi_minus_x0) - (coords(:, k1) - coords(:, 1))
        enddo

    end subroutine get_u_prim

    subroutine get_f_glob(phi_rp, f_prim, f_glob)
    implicit none
        double precision, intent(in)    :: phi_rp(:)
        double precision, intent(in)    :: f_prim(:)
        double precision, intent(inout) :: f_glob(:)
        
        integer                         :: num_nodes        ! Number of nodes
        integer                         :: i1, i2, k1       ! Iterators
        double precision                :: rot_mat(3,3)     ! Rotation matrix
        double precision                :: xi_minus_x0(3)   ! Vector from current wheel center to 
                                                            ! current node position
        
        num_nodes = (size(f_prim)-3)/3
        
        rot_mat = get_rotation_matrix(phi_rp)
        
        do k1=0,num_nodes   ! Torque rotated the same way as forces
            i1 = 3*k1 + 1
            i2 = i1 + 2
            f_glob(i1:i2) = matmul(rot_mat, f_prim(i1:i2))
        enddo

    end subroutine get_f_glob

    subroutine get_k_glob(phi_rp, k_glob)
    use uel_stiff_mod, only : uel_stiffness!, print_uel_time
    implicit none
        double precision, intent(in)                :: phi_rp(:)
        double precision, intent(inout)             :: k_glob(:,:)
        double precision                            :: rot_mat(3,3)         ! Rotation matrix
        double precision                            :: rot_mat_t(3,3)  ! Transpose rotation matrix
        integer                                     :: ndof,nnod
        integer                                     :: i_n,j_n
        integer                                     :: i_d(3),j_d(3)
        
        rot_mat = get_rotation_matrix(phi_rp)
        rot_mat_t = transpose(rot_mat)
        ndof = size(k_glob,1)
        nnod = ndof/3
        ! Leftmost index change fastest, hence we have that in the inner loop
        do j_n=1,nnod
            j_d = 3*(j_n-1) + [1,2,3]
            do i_n=1,nnod
                i_d = 3*(i_n-1) + [1,2,3]
                !k_d = i_d
                !l_d = j_d 
                !k_glob(i_d,j_d) = matmul(matmul(Q(i_d,i_d), uel_stiffness(k_d,l_d)), transpose(Q(j_d, j_d)))
                k_glob(i_d,j_d) = matmul(matmul(rot_mat, uel_stiffness(i_d,j_d)), rot_mat_t)
            enddo
        enddo
        
        ! Reference with full loop (to help understand code):
        !do i_n=1,nnod
        !    i_d = 3*(i_n-1) + [1,2,3]
        !    do j_n=1,nnod
        !        j_d = 3*(j_n-1) + [1,2,3]
        !        do k_n=1,nnod
        !            k_d = 3*(k_n-1) + [1,2,3]
        !            do l_n=1,nnod
        !                l_d = 3*(l_n-1) + [1,2,3]
        !                ! Q(i_d,k_d) = 0 unless i_n=k_n
        !                ! Q(j_d,l_d) = 0 unless j_n=l_n
        !                k_glob(i_d,j_d) = k_glob(i_d,j_d) + matmul(matmul(Q(i_d,k_d), uel_stiffness(k_d,l_d)), transpose(Q(l_d, j_d)))
        !            enddo
        !        enddo
        !    enddo
        !enddo
    end subroutine get_k_glob

    ! Internal procedures
    function get_rotation_matrix(phi_rp) result(rot_mat)
    implicit none
        double precision, intent(in)    :: phi_rp(:)        ! Rotation (either 1 (2d) or 3 (3d) comp)
        double precision, allocatable   :: rot_mat(:,:)     ! Rotation matrix (2x2 (2d) or 3x3 (3d)
        if (size(phi_rp) == 1) then ! 2d
            allocate(rot_mat(2,2))
            rot_mat(1, :) = [cos(phi_rp(1)), -sin(phi_rp(1))]
            rot_mat(2, :) = [sin(phi_rp(1)), cos(phi_rp(1))]
        elseif (size(phi_rp) == 3) then ! 3d, but account only for rotation around x-axis
            allocate(rot_mat(3,3))
            rot_mat(1, :) = [1.d0, 0.d0, 0.d0]
            rot_mat(2, :) = [0.d0, cos(phi_rp(1)), -sin(phi_rp(1))]
            rot_mat(3, :) = [0.d0, sin(phi_rp(1)), cos(phi_rp(1))]
        else
            write(*,*) 'phi_rp must have length 1 or 3 in "get_rotation_matrix"'
            write(*,*) 'size(phi_rp) = ', size(phi_rp)
            call xit()
        endif

    end function get_rotation_matrix

end module uel_trans_mod


! Unused modules, keep for reference and potentially for testing:
    ! subroutine get_k_glob_slow(phi_rp, k_glob)
    ! use uel_stiff_mod
    ! implicit none
        ! double precision, intent(in)    :: phi_rp(:)
        ! double precision, intent(inout) :: k_glob(:,:)
        
        ! double precision, allocatable   :: exp_rot_mat(:,:)
        
        ! ! This a very inefficient procedure for large matrices, as exp_rot_mat is (1) diagonal with 
        ! ! band width 2 or 3, and (2) contains a repeated pattern. This could therefore be sped up, but 
        ! ! on the other hand this might not be performance critical. It should be evaluated though...
        ! call print_uel_time('get_k_glob start = ')
        ! call get_expanded_rotation_matrix(phi_rp, size(uel_stiffness,1), exp_rot_mat)
        ! call print_uel_time('get_k_glob middle = ')
        ! k_glob = matmul(matmul(exp_rot_mat, uel_stiffness), transpose(exp_rot_mat))
        ! call print_uel_time('get_k_glob end = ')
    ! end subroutine get_k_glob_slow
    
    ! subroutine get_expanded_rotation_matrix(phi_rp, ndof, exp_rot_mat)
    ! implicit none
        ! double precision, intent(in)                :: phi_rp(:)        ! Rotation (either 1 (2d) or 3 
                                                                        ! !(3d) comp)
        ! integer, intent(in)                         :: ndof             ! Number of degrees of freedom
        ! double precision, allocatable, intent(out)  :: exp_rot_mat(:,:) ! Expanded rotation matrix 
                                                                        ! ! (ndof x ndof)
                                                                        
        ! integer                                     :: k1               ! Iterator
        ! double precision, allocatable               :: rot_mat(:,:)     ! Rotation matrix
        ! integer                                     :: num_node_dofs    ! Number of dofs per node

        ! allocate(exp_rot_mat(ndof,ndof))
        ! allocate(rot_mat, source=get_rotation_matrix(phi_rp))

        ! num_node_dofs = size(rot_mat,1)

        ! if (num_node_dofs == 2) then     ! 2d, rotation handled as special case
            ! exp_rot_mat(1:num_node_dofs, 1:num_node_dofs) = rot_mat
            ! exp_rot_mat(3,3) = 1.d0
            ! do k1=4,ndof,num_node_dofs
                ! exp_rot_mat(k1:(k1+num_node_dofs), k1:(k1+num_node_dofs)) = rot_mat
            ! enddo
        ! else                            ! 3d, no special treatment required
            ! do k1=1,ndof,num_node_dofs
                ! exp_rot_mat(k1:(k1+num_node_dofs-1), k1:(k1+num_node_dofs-1)) = rot_mat
            ! enddo
        ! endif
        
    ! end subroutine get_expanded_rotation_matrix