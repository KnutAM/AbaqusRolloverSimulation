module bc_mod
use abaqus_utils_mod
implicit none
    
contains

subroutine set_bc(contact_node_disp, wheel_rp_disp, rail_rp_disp, cycle_nr)
use load_param_mod, only : update_cycle, get_rolling_par, set_rp_bc, set_contact_node_bc
use node_id_mod, only : get_angle_incr, get_mesh_size, get_element_order, get_inds, &
                        get_node_coords, get_node_dofs
use find_mod, only : find
implicit none
    double precision, intent(in)    :: contact_node_disp(:,:,:) ! Contact node disp after rolling
    double precision, intent(in)    :: wheel_rp_disp(:)         ! Wheel rp disp after rolling
    double precision, allocatable, intent(inout) :: rail_rp_disp(:) ! Rail rp disp after rolling
                                                                    ! If not allocated, not used, 
                                                                    ! but it will then be allocated
                                                                    ! to zero.
    integer, intent(in)             :: cycle_nr                 ! Current rollover cycle
    
    double precision                :: rail_length              ! Rail length
    double precision                :: rot_per_length           ! Rotation per rolling length for coming cycle
    double precision                :: rail_extension           ! Rail extension for coming cycle
    integer                         :: num_elem_roll            ! Number of wheel elements rolled
    double precision                :: return_angle             ! Wheel rp angle to return to
    
    double precision                :: dx_rp(3)                 ! Translation of wheel reference point
    double precision                :: u_rp_start(6)
    double precision                :: u_rp_end(6)
    
    integer                         :: mesh_size(2)
    integer                         :: mesh_inds(2)
    integer                         :: element_order            ! Element order (1 or 2)    
    integer                         :: num_ind_roll             ! Number of node inds rolled
                                                                ! element_order*num_elem_roll
    integer                         :: na                       ! Number of contact nodes along angular direction
    integer                         :: old_ang_ind              ! Iterator for old nodes in contact, ang dir
    integer                         :: new_ang_ind              ! Iterator for new nodes in contact, ang dir
    integer                         :: nx                       ! Number of contact nodes along x-direction
    integer                         :: dx                       ! Increment in x index
    integer                         :: nt                       ! Total number of contact nodes
    integer                         :: n_el_x, n_el_a           ! Elements along x and ang direction    
    integer                         :: x_ind                    ! Iterator for nodes along x-direction
    integer                         :: num_c_dofs               ! Number of constrained dofs
    integer, allocatable            :: cdofs(:), fdofs(:)       ! List of constrained and free dofs indices
    double precision, allocatable   :: ubc(:), uf(:)            ! List of constrained and free dof values
    integer                         :: k_cdofs(3)               ! Dof counter for constrained nodes
    integer                         :: node_dofs(3)             ! Temporary storage for node dofs
    integer                         :: fdof_inds(3)             ! Indices for the dofs in fdofs
    
    double precision                :: x0_new(3)                ! Initial coordinates for a new node in contact
    double precision                :: x_old(3)                 ! Current coordinates for a old node in contact (before move back)
    double precision                :: x_new(3)                 ! Current coordinates for a new node in contact (after move back)
    double precision                :: u_new(3)                 ! Displacements for a new node in contact, u_new=x_new-x0_new
    
    ! Update load parameters for the present cycle
    call update_cycle(cycle_nr+1)
    
    ! Get load parameters for the present cycle
    call get_rolling_par(rail_length, rot_per_length, rail_extension)
    
    ! Calculate motion for the reference point
    !  Linear motion
    if (.not.allocated(rail_rp_disp)) then  ! we don't use it, set it to zero for no effect.
        allocate(rail_rp_disp(6))
        rail_rp_disp = 0.d0
    endif
        
    !  Note, no account for rail rp rotation taken into account, this could be generalized but requires the rail height. 
    dx_rp = [0.d0, 0.d0, - (rail_length + rail_rp_disp(3))] 
    !  Rotational motion
    num_elem_roll = nint(wheel_rp_disp(4)/get_angle_incr())
    return_angle = wheel_rp_disp(4) - num_elem_roll*get_angle_incr()
    
    u_rp_start = 0.d0
    u_rp_start(1:3) = wheel_rp_disp(1:3) + dx_rp
    u_rp_start(4) = return_angle
    
    u_rp_end = u_rp_start
    u_rp_end(3) = u_rp_start(3) + rail_length + rail_extension
    u_rp_end(4) = u_rp_start(4) + (u_rp_end(3)-u_rp_start(3))*rot_per_length
    
    ! Set boundary conditions for the reference point
    call set_rp_bc(wheel_rp_disp, u_rp_start, u_rp_end)
    
    ! Set boundary conditions for the wheel contact nodes
    element_order = get_element_order()
    mesh_size = get_mesh_size()
    na = mesh_size(1) ! Number of nodes in angular direction on wheel
    nx = mesh_size(2)   ! Number of nodes in x-direction on wheel
    
    
    num_ind_roll = element_order*num_elem_roll
    
    if (element_order == 1) then
        !nt = (n_el_a+1)*(n_el_x+1)
        num_c_dofs = 6 + 3*(na - num_ind_roll)*nx
    else
        !nt = (2*n_el_a+1)*(2*n_el_x+1) - (n_el_a*n_el_x)
        !nt = 3*n_el_a*n_el_x + 2*(n_el_a+n_el_x) + 1
        !nt = n_el_a*(3*n_el_x + 2) + 2*n_el_x + 1
        n_el_x = (nx-1)/element_order
        n_el_a = (na-1)/element_order
        num_c_dofs = 6 + 3*((n_el_a-num_elem_roll)*(3*n_el_x + 2) + 2*n_el_x + 1)
    endif
    
    
    allocate(ubc(num_c_dofs), cdofs(num_c_dofs))
    ubc(1:6) = u_rp_start
    cdofs(1:6) = [1,2,3,4,5,6]
    k_cdofs = [4,5,6]
    dx = element_order
    
    do old_ang_ind=1,(na-num_ind_roll)
        new_ang_ind = old_ang_ind + num_ind_roll
        
        if (element_order == 2) then
            if (dx == 2) then
                dx = 1
            else
                dx = 2
            endif
        endif
        
        do x_ind = 1,nx,dx
            x0_new = get_node_coords([new_ang_ind, x_ind])
            x_old = get_node_coords([old_ang_ind, x_ind]) + contact_node_disp(:, old_ang_ind, x_ind)
            x_new = x_old + dx_rp
            u_new = x_new - x0_new
            call set_contact_node_bc([new_ang_ind, x_ind], u_new)
            k_cdofs = k_cdofs + 3
            cdofs(k_cdofs) = get_node_dofs([new_ang_ind, x_ind])
            ubc(k_cdofs) = u_new
        enddo
    enddo
    
    call get_fdofs(ubc, cdofs, uf, fdofs)
    do old_ang_ind=1,num_ind_roll
        do x_ind = 1,nx
            node_dofs = get_node_dofs([old_ang_ind, x_ind])
            fdof_inds = find(fdofs, node_dofs(1)) + [0, 1, 2]
            call set_contact_node_bc([old_ang_ind, x_ind], uf(fdof_inds))
        enddo
    enddo
    
end subroutine

subroutine get_fdofs(ubc, cdofs, uf, fdofs)
use uel_stiff_mod, only : get_ndof
use uel_trans_mod, only : get_phi, get_k_glob
implicit none
    double precision, intent(in)                :: ubc(:)   ! Displacements already calculated
    integer, intent(in)                         :: cdofs(:) ! Location of ubc in stiffness matrix
    integer, allocatable, intent(out)           :: fdofs(:) ! Location of uf in stiffness matrix
    double precision, allocatable, intent(out)  :: uf(:)    ! Displacements to be calculated
    
    double precision, allocatable               :: kstiff(:,:), kff(:,:)
    double precision                            :: phi_rp(3)
    integer                                     :: num_dof
    integer                                     :: num_fdof
    integer                                     :: dof, fdof_ind
    integer, allocatable                        :: ipiv(:)  ! Pivot indices for LU decomposition
    integer                                     :: info     ! Check of dgesv success
    
    num_dof = get_ndof()
    num_fdof = num_dof - size(cdofs)
    
    allocate(kstiff(num_dof,num_dof))
    allocate(fdofs(num_fdof), uf(num_fdof), ipiv(num_fdof), kff(num_fdof,num_fdof))
    
    ! Get rotated element stiffness matrix
    phi_rp = get_phi(ubc)
    call get_k_glob(phi_rp, kstiff)
    
    ! Get the free degrees of freedom to be calculated
    ! This could be sped up by looping over the nodes instead as each node has 3 consecutive dofs...
    fdof_ind = 0
    do dof=1,num_dof
        if (.not.any(cdofs==dof)) then
            fdof_ind = fdof_ind + 1
            fdofs(fdof_ind) = dof
        endif
    enddo
    
    ! |ff| = |Kff Kfc| |uf| = | 0|  Nodes with fdofs are not in contact, i.e. no external load, ff=0
    ! |fc| = |Kcf Kcc| |uc| = |fc|  Nodes with cdofs are prescribed, i.e. external loads, fc
    ! Kff*uf = -Kfc*uc
    uf = -matmul(kstiff(fdofs, cdofs), ubc)  !Input b in dgesv is overwritten to answer x
    kff = kstiff(fdofs, fdofs)
    !    dgesv(       n, nrhs,   a,      lda, ipiv,  b,      ldb, info )
    call dgesv(num_fdof,    1, kff, num_fdof, ipiv, uf, num_fdof, info)
    if (info /= 0) then
        write(*,*) 'Could not solve for wheel displacements'
        call xit()
    endif
    
end subroutine

end module bc_mod
