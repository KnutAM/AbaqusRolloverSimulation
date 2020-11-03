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
    
    double precision, allocatable   :: ubc(:)       ! Degree of freedom vector to be prescribed
    double precision, allocatable   :: uf(:)        ! Degree of freedom vector to be determined
    integer, allocatable            :: cdofs(:)     ! Dof numbers of constrained dofs
    integer                         :: nfdofs       ! Number of dofs that are "free"
    integer                         :: dofind           ! Temp variable for current dof number
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
    write(filename, "(A, A, I0, A)") trim(filename), '/bc_cycle', cycle_nr, '.txt'
    
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
    allocate(ubc(3+2*(nnod-num_elem_roll)), cdofs(3+2*(nnod-num_elem_roll)))
    ubc(1:2) = u_new_rp
    ubc(3) = return_angle
    cdofs(1:3) = [1,2,3]
    do old_ind=1,(nnod-num_elem_roll)
        new_ind = old_ind + num_elem_roll   ! HERE WE SHOULD MULTIPLY BY NUM NODES PER ANGLE ROW
        x0_new = node_c(:, new_ind) - node_u(:, new_ind)
        x_old = node_c(:, old_ind)
        
        !x_new = x_rp_new + (x_old - x_rp_old) = x_old + dx_rp  (4)
        x_new = x_old + dx_rp
        u_new = x_new - x0_new
        write(file_id, "(I0, 2ES25.15)") node_n(new_ind), u_new(1), u_new(2)
        ! Add calculated constrained dofs
        dofind = 3 + (old_ind-1)*2 + 1
        ubc(dofind:(dofind+1)) = u_new
        cdofs(dofind:(dofind+1)) = 3 + (new_ind-1)*2 + [1, 2]
    enddo
    
    nfdofs = 2*num_elem_roll
    call get_fdofs(uf, nfdofs, ubc, cdofs)
    
    do old_ind=1,num_elem_roll
        dofind = 2*(old_ind-1) + 1
        write(file_id, "(I0, 2ES25.15)") node_n(old_ind), uf(dofind), uf(dofind+1)
    enddo
    
    close(file_id)
    
end subroutine

subroutine get_fdofs(uf, nfdofs, ubc, cdofs)
use wheel_super_element_mod
implicit none
    double precision, allocatable, intent(out)  :: uf(:)    ! Displacements to be calculated
    integer, intent(in)                         :: nfdofs   ! Number of displcements to be calculated
    double precision, intent(in)                :: ubc(:)   ! Displacements already calculated
    integer, intent(in)                         :: cdofs(:) ! Location of ubc in stiffness matrix
    
    double precision, allocatable               :: kprim(:,:), kstiff(:,:), kff(:,:)
    double precision                            :: rotation
    integer                                     :: ndof
    integer                                     :: f1, f2   ! First and last "free" dof
    integer, allocatable                        :: ipiv(:)  ! Pivot indices for LU decomposition
    integer                                     :: info     ! Check of dgesv success
    
    ndof = size(ubc) + nfdofs
    allocate(kprim(ndof,ndof), kstiff(ndof,ndof), uf(nfdofs), ipiv(nfdofs), kff(nfdofs,nfdofs))
    
    rotation = ubc(3)
    
    ! Call routines from wheel_super_element_mod
    call get_unrotated_stiffness(kprim)
    call rotate_stiffness(rotation, kprim, kstiff)
    
    ! |ff| = |Kff Kfc| |uf| = | 0|
    ! |fc| = |Kcf Kcc| |uc| = |fc|
    ! Kff*uf = -Kfc*uc
    f1 = 4
    f2 = 3 + nfdofs
    uf = -matmul(kstiff(f1:f2, cdofs), ubc)  !Input b in dgesv is overwritten to answer x
    kff = kstiff(f1:f2, f1:f2)
    !    dgesv(     n, nrhs,   a,    lda, ipiv,  b,    ldb, info )
    call dgesv(nfdofs,    1, kff, nfdofs, ipiv, uf, nfdofs, info)

    if (info /= 0) then
        write(*,*) 'Could not solve for wheel displacements'
        call xit()
    endif
    
end subroutine

end module bc_mod
