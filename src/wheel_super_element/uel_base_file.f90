!DEC$ FREEFORM
!   First 3 dofs are x-disp, y-disp, z-rot for wheel center
!   The remaining dofs are x, y disp of wheel perimeter nodes
!
!   Parameters
!   props(1)                    Young's modulus

! - Variables that always should be updated
!   rhs         [ndof]          external - internal forces
!   amatrx      [ndof,ndof]     jacobian
!   svars       [nsvars]        Solution-dependent state variables       
!   energy      [8]             Energy values (old values given at input, to be updated to after incr)
!               [Kinetic energy, Elastic strain energy, Creep dissipation, plastic dissipation, 
!                viscous dissipation, Artificial strain energy (due to e.g. hourglass stiffness),
!                electrostatic energy, incremental work done by loads applied within the uel]
!
! - Variables that can be updated
!   pnewdt                      Ratio of suggested new time increment
!
! - Variables passed for information (DO NOT CHANGE)
!   props       [nprops]        Floating point array of property values
!   jprops      [njprop]        Integer point array of property values
!   coords      [3,nnod]        Coordinates of the nodes in the element
!   u           [ndof]          dof values at the end of the increment
!   du          [ndof]          incremental values for the dofs
!   v           [ndof]          du/dt (only defined for lflags(1)=11 or 12)
!   a           [ndof]          d^2u/dt^2 (only defined for lflags(1)=11 or 12)
!   jdltyp      [?]             See manual
!   adlmag      [?]             See manual
!   ddlmag      [?]             See manual
!   predef      [2,?,nnod]      Predefined field variables
!   params      [?]             Params associated with the solution procedure (see manual)
!   lflags      [7]             Flags that define the current solution procedure and element requirements
!   time        [2]             Value of [step time, total time] at the beginning of the current increment
!   dtime       [dbl]           Time increment
!   period      [dbl]           Time period of the current step
!   ndofel      [int]           ndof for element
!   mlvarx      [int]           Dimensioning parameter used when several displacement or right-hand-side vectors are used. 
!   nrhs        [int]           Number of load vectors. NRHS is 1 in most nonlinear problems: it is 
!                               2 for the modified Riks static procedure (Static stress analysis), 
!                               and it is greater than 1 in some linear analysis procedures and during substructure generation. 
!   nsvars      [int]           User-defined number of solution-dependent state variables associated with the element
!   nprops      [int]           User-defined number of real property values associated with the element
!   njprop      [int]           User-defined number of integer property values associated with the element
!   mcrd        [int]           Defined as the maximum of the user-defined maximum number of coordinates 
!                               needed at any node point (Defining the maximum number of coordinates 
!                               needed at any nodal point) and the value of the largest active degree 
!                               of freedom of the user element that is less than or equal to 3. For 
!                               example, if you specify that the maximum number of coordinates is 1 
!                               and the active degrees of freedom of the user element are 2, 3, and 6, 
!                               MCRD will be 3. If you specify that the maximum number of coordinates 
!                               is 2 and the active degrees of freedom of the user element are 11 and 12, MCRD will be 2. 
!   nnode       [int]           User-defined number of nodes on the element
!   jtype       [int]           Integer defining the element type. This is the user-defined integer value n in element type Un
!   kstep       [int]           Step number
!   kinc        [int]           Increment number
!   jelem       [int]           User-assigned element number. 
!   ndload      [int]           Identification number of the distributed load or flux currently active on this element. 
!   mdload      [int]           Total number of distributed loads and/or fluxes defined on this element. 
!   npredf      [int]           Number of predefined field variables, including temperature. For user 
!                               elements Abaqus/Standard uses one value for each field variable per node. 
module uel_mod
implicit none
    
    contains
    
subroutine check_analysis_type(lflags)
implicit none
    integer, intent(in) :: lflags(:)
    write(*,*) 'procedure type:', lflags(1)
    if (lflags(2)==1) then
        write(*,*) 'small strains used'
    else
        write(*,*) 'finite strains used'
    endif
    select case (lflags(3))
        case (1)
            write(*,*) 'Normal implicit time incrementation procedure'
        case (2)
            write(*,*) 'Define current stiffness matrix'
        case (3)
            write(*,*) 'Define current damping matrix'
        case (4)
            write(*,*) 'Define current mass matrix'
        case (5)
            write(*,*) 'Define the current residual or load vector only'
        case (6)
            write(*,*) 'Define the current mass matrix and the residual vector for the initial acceleration calculation'
        case (100)
            write(*,*) 'Define perturbation quantities for output.'
        case default
            write(*,*) 'Uknown lflags(3) = ', lflags(3)
    end select
    if (lflags(4)==0) then
        write(*,*) 'This is a general step'
    else
        write(*,*) 'This is a linear pertubation step'
    endif
    if (lflags(5)==0) then
        write(*,*) 'The current approximations to u were based on Newton corrections'
    else
        write(*,*) 'The current approximations to u were found by extrapolation from the previous increment'
    endif
    if (lflags(7)==1) then
        write(*,*) 'When the damping matrix flag is set, the viscous damping matrix is defined. '
    else
        write(*,*) 'When the damping matrix flag is set, the structural damping matrix is defined.'
    endif
end subroutine

subroutine uel_output(u, ndofel, nnode, lflags, kinc)
implicit none
    double precision, intent(in)    :: u(:)
    integer, intent(in)             :: ndofel, nnode, lflags(:), kinc
    integer                         :: k1, kmax
    
    kmax = 1
    do k1=2,ndofel
        if (abs(u(k1))>abs(u(kmax))) then
            kmax=k1
        endif
    enddo
    
    write(*,*) '--- start uel output ---'
    write(*,*) 'ndofel = ', ndofel
    write(*,*) 'nnode = ', nnode
    write(*,*) 'umax = ', u(kmax), '(u(', kmax, '))'
    call check_analysis_type(lflags)
    write(*,*) 'kinc = ', kinc
    write(*,*) 'u:'
    write(*,*) u
    write(*,*) '--- end uel output ---'
    
end subroutine uel_output
    
end module uel_mod

module wheel_super_element_mod
implicit none

contains
    double precision, parameter :: PI=2.0*asin(1.0)

function rot_mat(angle) return(Q)
implicit none
    double precision, intent(in)    :: angle
    double precision                :: Q(2,2)
    
    Q(1, :) = [cos(rotation_angle), sin(rotation_angle)]
    Q(2, :) = [-sin(rotation_angle), cos(rotation_angle)]
    
end function rot_mat
    

subroutine get_uprim(coords, u, uprim)    
! Transform the nodal displacements into local (rotated) coordinate system
implicit none
    double precision, intent(in)    :: coords(:,:), u(:)
    double precision, allocatable   :: uprim(:)
    double precision                :: Qt(2,2), x0_minus_xi(2)
    integer                         :: nnods, k1, i1, i2
    
    nnods = (size(u)-3)/2
    Qt = transpose(rot_mat(rotation))
    allocate(uprim(2*nnods+1))
    uprim(1:3) = 0.0
    do k1=2,nnod
        i1 = 2*k1
        i2 = 2*k1 + 1
        x0_minus_xi = coords(1:2, k1) + u(i1:i2) - (coords(1:2, 1) + u(1:2))
        uprim(i1:i2) = matmul(Qt, x0_minus_xi) - (coords(1:2, k1) - coords(1:2, 1))
    enddo
    
end subroutine get_uprim
    
subroutine get_F_gcs(rotation, Fprim, rhs)
! Transform nodal force vector into global coordinate system
implicit none
    double precision, intent(in)    :: rotation, Fprim(:)
    double precision, intent(inout) :: rhs(:,:)
    double precision                :: Q(2,2)
    integer                         :: nnods, k1, i1, i2
    
    nnods = (size(Fprim)-3)/2
    Q = rot_mat(rotation)
    rhs(1:2, 1) = matmul(Q, Fprim(1:2))
    rhs(3, 1) = Fprim(3)    ! Torque not affected by rotation
    do k1=2,nnods
        i1 = 2*k1
        i2 = 2*k1 + 1
        rhs(i1:i2, 1) = matmul(Q, Fprim(i1:i2))
    enddo
    
    
end subroutine get_F_gcs

subroutine get_rotation_matrix(rotation_angle, ndof, rotation_matrix)
implicit none
    double precision, intent(in)    :: rotation_angle
    integer, intent(in)             :: ndof
    double precision, allocatable   :: rotation_matrix(:,:)
    integer                         :: k1, k2
    double precision                :: rotation_sub_matrix(2,2)
    
    allocate(rotation_matrix(ndof,ndof))
    
    rotation_sub_matrix = rot_mat(rotation_angle)
    
    rotation_matrix(1:2, 1:2) = rotation_sub_matrix
    do k1=1,(ndof-3)/2
        k2 = 3 + 2*k1 - 1
        rotation_matrix(k2:(k2+1), k2:(k2+1)) = rotation_sub_matrix
    enddo
    
end subroutine get_rotation_matrix

subroutine get_rotation_matrix_derivative(rotation_angle, ndof, rotation_matrix_diff)
implicit none
    double precision, intent(in)    :: rotation_angle
    integer, intent(in)             :: ndof
    double precision, allocatable   :: rotation_matrix(:,:)
    
    !sin(a+pi/2)=cos(a)
    !cos(a+pi/2)=-sin(a)
    call get_rotation_matrix(rotation_angle + PI/2.0, ndof, rotation_matrix_diff)
    
end subroutine

subroutine get_u_diff(du0m_du, ndofel)
implicit none
    integer, intent(out)    :: du0m_du(:, :)
    integer, intent(in)     :: ndofel
    
    allocate(du0m_du(ndofel, 2))
    
    du0m_du = 0
    du0m_du(1,1) = 1
    du0m_du(2,2) = 1
    do k1=1,((ndofel-3)/2)
        du0m_du(2*k1+2,1) = 1
        du0m_du(2*k1+3,2) = 1
    enddo
    
end subroutine get_u_diff

subroutine get_x_diff(u, coords, xi_minus_x0, xi_init_minus_x0_init)
implicit none
    double precision, intent(in)    :: u(:), coords(:,:)
    double precision, allocatable   :: xi_minus_x0(:), xi_init_minus_x0_init(:)
    integer                         :: ndofel, k1, k2
    
    ndofel = size(u)
    
    allocate(xi_minus_x0(ndofel), xi_init_minus_x0_init(ndofel))
    
    xi_minus_x0(1:3) = 0.0
    xi_init_minus_x0_init(1:3) = 0.0
    
    do k1=1,((ndofel-3)/2)
        do k2=1,2
            xi_init_minus_x0_init(1 + 2*k1 + k2) = coords(k2,k1+1) - coords(k2,1)
            xi_minus_x0(1 + 2*k1 + k2) = coords(k2,k1+1) + u(2 + 2*k1) - (coords(k2,1) + u(k2))
        enddo
    enddo
        

end subroutine
    
subroutine get_stiffness(u, Kprim, coords, amatrx)
implicit none
    double precision, intent(in)    :: u(:), Kprim(:,:), coords(:,:)
    double precision, intent(inout) :: amatrx(:,:)
    
    double precision                :: rotation
    double precision, allocatable   :: QK(:,:), xi_minus_x0(:), xi_init_minus_x0_init(:)
    integer, allocatable            :: du0m_du(:,:)
    integer                         :: ndofel, k1

    ndofel = size(u)
    allocate(QK(ndofel, ndofel))
    
    call get_u_diff(du0m_du, ndofel)
    call get_x_diff(u, coords, xi_minus_x0, xi_init_minus_x0_init)
        
    rotation = u(3)
    call get_rotation_matrix(rotation, ndofel, rotation_matrix)
    call get_rotation_matrix_derivative(rotation, ndofel, rotation_matrix_diff)
    
    
    QK = matmul(rotation_matrix, Kprim)
    amatrx = matmul(QK, transpose(rotation_matrix))
    amatrx(:, 1:2) = amatrx(:, 1:2) - matmul(amatrx, du0m_du)
    amatrx(:, 3) = amatrx(:, 3) - matmul(QK, rotation_matrix(:,3))
    amatrx(:, 3) = amatrx(:, 3) &
                 + matmul(matmul(rotation_matrix_diff, transpose(QK)),xi_minus_x0) &
                 - matmul(matmul(rotation_matrix_diff,Kprim),xi_init_minus_x0_init)
    amatrx(:, 3) = amatrx(:, 3) + matmul(matmul(QK, rotation_matrix_diff), xi_minus_x0)
    
end subroutine

subroutine get_stiffness_matrix(ke)
implicit none
    double precision    :: ke(:,:)
    
    !<ke_to_be_defined_by_python_script>
    
end subroutine

end module wheel_super_element_mod
    

subroutine uel(rhs,amatrx,svars,energy,ndofel,nrhs,nsvars,&
               props,nprops,coords,mcrd,nnode,u,du,v,a,jtype,time,dtime,&
               kstep,kinc,jelem,params,ndload,jdltyp,adlmag,predef,npredf,&
               lflags,mlvarx,ddlmag,mdload,pnewdt,jprops,njprop,period)
    use uel_mod
    use wheel_super_element_mod
    implicit none
    double precision, intent(inout) :: rhs(ndofel,1), amatrx(ndofel,ndofel), svars(nsvars), energy(8), pnewdt
    double precision, intent(in)    :: props(nprops), coords(mcrd,nnode)
    double precision, intent(in)    :: u(ndofel), du(ndofel,1), v(ndofel), a(ndofel)
    double precision, intent(in)    :: time(2), dtime, period, params(:)
    double precision, intent(in)    :: jdltyp(:,:), adlmag(:,:), ddlmag(:,:)
    double precision, intent(in)    :: predef(2,npredf,nnode)
    integer, intent(in)             :: ndofel, nrhs, nsvars, nprops, njprop, mcrd, nnode, jtype, kstep, kinc
    integer, intent(in)             :: jelem, ndload, mdload, npredf, jprops(njprop), lflags(7), mlvarx
      
    double precision, allocatable   :: rotation_matrix(:,:), rotation_matrix_diff(:,:), Kprim(:,:)
    double precision, allocatable   :: uprim(:), Fprim(:)
    double precision                :: rotation
    integer                         :: k1, kmax
    
    rotation = u(3)
    
    allocate(Kprim(ndofel, ndofel))
    call get_stiffness_matrix(Kprim)    ! Get unrotated stiffness from static condensation
    Kprim = Kprim*props(1)              ! Scale with Elastic modulus
    
    allocate(uprim(ndofel), Fprim(ndofel))
    call get_uprim(coords, u, uprim)    
    Fprim = matmul(Kprim, uprim)
    call get_F_gcs(rotation, Fprim, rhs)
    
    
    call get_stiffness(u, Kprim, coords, amatrx)
    
    write(*,*) 'check norm of antisymmetric part of Kel:'
    write(*,*) sum((amatrx-transpose(amatrx))**2)
    
    call uel_output(u, ndofel, nnode, lflags, kinc)
    
end subroutine uel