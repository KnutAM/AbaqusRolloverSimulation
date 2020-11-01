! Module for transforming user element for rotations
module uel_trans_mod
implicit none

    private

    public :: get_phi!(u, phi_rp)
    public :: get_u_prim!(coords, u, u_prim)
    public :: get_f_glob!(phi_rp, f_prim, f_glob)
    public :: get_k_glob!(phi_rp, k_glob)

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
    use uel_stiff_mod
    implicit none
        double precision, intent(in)    :: phi_rp(:)
        double precision, intent(inout) :: k_glob(:,:)
        
        double precision, allocatable   :: exp_rot_mat(:,:)
        
        ! This a very inefficient procedure for large matrices, as exp_rot_mat is (1) diagonal with 
        ! band width 2 or 3, and (2) contains a repeated pattern. This could therefore be sped up, but 
        ! on the other hand this might not be performance critical. It should be evaluated though...
        
        call get_expanded_rotation_matrix(phi_rp, size(uel_stiffness,1), exp_rot_mat)
        k_glob = matmul(matmul(exp_rot_mat, uel_stiffness), transpose(exp_rot_mat))
        
    end subroutine get_k_glob

    ! Internal procedures
    subroutine get_expanded_rotation_matrix(phi_rp, ndof, exp_rot_mat)
    implicit none
        double precision, intent(in)                :: phi_rp(:)        ! Rotation (either 1 (2d) or 3 
                                                                        !(3d) comp)
        integer, intent(in)                         :: ndof             ! Number of degrees of freedom
        double precision, allocatable, intent(out)  :: exp_rot_mat(:,:) ! Expanded rotation matrix 
                                                                        ! (ndof x ndof)
                                                                        
        integer                                     :: k1               ! Iterator
        double precision, allocatable               :: rot_mat(:,:)     ! Rotation matrix
        integer                                     :: num_node_dofs    ! Number of dofs per node

        allocate(exp_rot_mat(ndof,ndof))
        allocate(rot_mat, source=get_rotation_matrix(phi_rp))

        num_node_dofs = size(rot_mat,1)

        if (num_node_dofs == 2) then     ! 2d, rotation handled as special case
            exp_rot_mat(1:num_node_dofs, 1:num_node_dofs) = rot_mat
            exp_rot_mat(3,3) = 1.d0
            do k1=4,ndof,num_node_dofs
                exp_rot_mat(k1:(k1+num_node_dofs), k1:(k1+num_node_dofs)) = rot_mat
            enddo
        else                            ! 3d, no special treatment required
            do k1=0,ndof,num_node_dofs
                exp_rot_mat(k1:(k1+num_node_dofs), k1:(k1+num_node_dofs)) = rot_mat
            enddo
        endif
        
    end subroutine get_expanded_rotation_matrix
        

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