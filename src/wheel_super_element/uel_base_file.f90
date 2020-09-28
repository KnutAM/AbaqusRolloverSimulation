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
    integer, intent(in) :: lflags(*)
    write(*,*) 'procedure type:', lflags(1)
    if (lflags(2)==0) then
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

subroutine uel_output(lflags, kinc, kstep, time)
implicit none
    integer, intent(in)             :: lflags(*), kinc, kstep
    double precision, intent(in)    :: time
    character(len=30)               :: output_request
    character(len=10)               :: clock_time_str
    
    call date_and_time(time=clock_time_str)
    
    if (lflags(3)==1) then
        output_request = 'residual and stiffness matrix'
    elseif (lflags(3)==2) then
        output_request = 'stiffness matrix'
    elseif (lflags(3)==4) then
        output_request = 'mass matrix'
    elseif (lflags(3)==5) then
        output_request = 'residual'
    else
        write(output_request, "(A,I1)") 'lflags(3)=', lflags(3)
    endif
    
    write(*,*) 'Wheel super element'
    write(*,"(A10, A10, A10, 5X, A30, 5X, A10)") 'step', 'kinc', 'time', 'req. output', 'clock'
    write(*,"(I10, I10, F10.4, 5X, A30, 5X, A10)") kstep, kinc, time, output_request, clock_time_str
    
    
end subroutine uel_output
    
end module uel_mod

module debug_mod    ! Module with functions not required for regular function of element
implicit none

    contains
    
subroutine print_nodal_contributions(coords, Fprim, kstep, kinc, time)
implicit none
    double precision, intent(in)    :: coords(:,:), Fprim(:), time(2)
    integer, intent (in)            :: kstep, kinc    
    double precision                :: torque
    double precision, allocatable   :: torque_contrib(:)    ! Torque contribution from each node
    double precision, allocatable   :: Fvec(:,:)            ! Force vector for each node
    double precision, allocatable   :: xrel(:,:)            ! Coordinates relative center
    double precision, allocatable   :: ang(:)               ! Node angles
    
    integer                         :: ncnod                ! Number of nodes on wheel circumference
    integer                         :: ndof                 ! Total number of dof
    integer                         :: k1, k2               ! Iterators
    
    ncnod = size(coords,2) - 1
    ndof = size(Fprim)
    allocate(torque_contrib(ncnod), Fvec(2,ncnod), xrel(2,ncnod), ang(ncnod))
    
    xrel(1,:) = coords(1,2:(ncnod+1)) - coords(1,1)
    xrel(2,:) = coords(2,2:(ncnod+1)) - coords(2,1)
    Fvec(1,:) = Fprim(4:ndof:2)
    Fvec(2,:) = Fprim(5:ndof:2)
    
    ang = atan2(xrel(2,:), xrel(1,:))*180.0/acos(-1.0)
    
    torque_contrib = xrel(1,:)*Fvec(2,:) - xrel(2,:)*Fvec(1,:)
    
    write(*,"(A, E15.3, E15.3, E15.3)") 'Fprim(1:3) = ', Fprim(1), Fprim(2), Fprim(3)
    
    write(*,"(A10, A10, A15, A15, A15)") 'num', 'ang', 'torque_contrib', 'Fx', 'Fy'
    do k1=1,ncnod
        write(*,"(I10, F10.1, E15.3, E15.3, E15.3)") k1, ang(k1), torque_contrib(k1), Fvec(1,k1), Fvec(2,k1)
    enddo
    
    write(*,"(A, E15.3)") 'F(3)                     = ', Fprim(3)
    write(*,"(A, E15.3)") 'Sum torque contributions = ', sum(torque_contrib)
    
end subroutine
    

end module debug_mod

module wheel_super_element_mod
implicit none
    double precision, parameter :: PI=2.0*asin(1.0)
contains    

function norm(m)
implicit none
    double precision    :: m(:,:)
    double precision    :: norm
        
    norm = sqrt(sum(m**2))
end function

subroutine get_F_gcs(rotation, Fprim, Fint)
! Transform nodal force vector into global coordinate system
implicit none
    double precision, intent(in)    :: rotation, Fprim(:)
    double precision, intent(inout) :: Fint(:)
    double precision                :: Q(2,2)
    integer                         :: nnods, k1, i1, i2
    
    nnods = (size(Fprim)-1)/2
    Q = rot_mat(rotation)
    Fint(1:2) = matmul(Q, Fprim(1:2))
    Fint(3) = Fprim(3)    ! Torque not affected by rotation
    do k1=2,nnods
        i1 = 2*k1
        i2 = i1 + 1
        Fint(i1:i2) = matmul(Q, Fprim(i1:i2))
    enddo
    
    
end subroutine get_F_gcs

subroutine get_uprim(coords, u, uprim)
! Transform the nodal displacements into local (rotated) coordinate system
implicit none
    double precision, intent(in)    :: coords(:,:), u(:)
    double precision, allocatable   :: uprim(:)
    double precision                :: Qt(2,2), xi_minus_x0(2)
    integer                         :: nnods, k1, i1, i2
    
    nnods = (size(u)-1)/2
    Qt = transpose(rot_mat(u(3)))
    allocate(uprim(size(u)))
    uprim(1:3) = 0.0
    do k1=2,nnods
        i1 = 2*k1
        i2 = i1 + 1
        xi_minus_x0 = coords(1:2, k1) + u(i1:i2) - (coords(1:2, 1) + u(1:2))
        uprim(i1:i2) = matmul(Qt, xi_minus_x0) - (coords(1:2, k1) - coords(1:2, 1))
    enddo
    
end subroutine get_uprim

function rot_mat(angle) result(Q)
implicit none
    double precision, intent(in)    :: angle
    double precision                :: Q(2,2)
    
    Q(1, :) = [cos(angle), -sin(angle)]
    Q(2, :) = [sin(angle), cos(angle)]
    
end function rot_mat

subroutine get_rotation_matrix(rotation_angle, ndof, rotation_matrix)
implicit none
    double precision, intent(in)    :: rotation_angle
    integer, intent(in)             :: ndof
    double precision, allocatable   :: rotation_matrix(:,:)
    integer                         :: k1, k2
    double precision                :: rotation_sub_matrix(2,2)
    
    allocate(rotation_matrix(ndof,ndof))
    
    rotation_sub_matrix = rot_mat(rotation_angle)
    rotation_matrix = 0.0
    
    rotation_matrix(1:2, 1:2) = rotation_sub_matrix
    rotation_matrix(3,3) = 1.0
    do k1=4,ndof,2
        rotation_matrix(k1:(k1+1), k1:(k1+1)) = rotation_sub_matrix
    enddo
    
end subroutine get_rotation_matrix

subroutine get_rotation_matrix_derivative(rotation_angle, ndof, rotation_matrix_diff)
implicit none
    double precision, intent(in)    :: rotation_angle
    integer, intent(in)             :: ndof
    double precision, allocatable   :: rotation_matrix_diff(:,:)
    
    !sin(a+pi/2)=cos(a)
    !cos(a+pi/2)=-sin(a)
    call get_rotation_matrix(rotation_angle + PI/2.0, ndof, rotation_matrix_diff)
    rotation_matrix_diff(3,3) = 0.0
    
end subroutine

subroutine get_u_diff(du0m_du, ndofel)
implicit none
    integer, allocatable    :: du0m_du(:, :)
    integer, intent(in)     :: ndofel
    integer                 :: k1
    
    allocate(du0m_du(ndofel, 2))
    
    du0m_du = 0
    du0m_du(1,1) = 1
    du0m_du(2,2) = 1
    do k1=4,ndofel,2
        du0m_du(k1,1) = 1
        du0m_du(k1+1,2) = 1
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
    
subroutine rotate_stiffness(rotation, Kprim, amatrx)
implicit none
    double precision, intent(in)    :: rotation, Kprim(:,:)
    double precision, intent(inout) :: amatrx(:,:)
    
    double precision, allocatable   :: rotation_matrix(:,:)

    call get_rotation_matrix(rotation, size(Kprim,1), rotation_matrix)
    
    amatrx = matmul(matmul(rotation_matrix, Kprim), transpose(rotation_matrix))
    
end subroutine

subroutine get_unrotated_stiffness(ke)
implicit none
    double precision    :: ke(:,:)
    
    !<ke_to_be_defined_by_python_script>
    
end subroutine

subroutine get_coords(coords)
implicit none
    double precision, allocatable    :: coords(:,:)
    
    !<coords_to_be_defined_by_python_script>

end subroutine 

subroutine check_coords(coords)
implicit none
    double precision, intent(in)    :: coords(:,:)
    double precision, allocatable   :: uel_coords_check(:,:)
    double precision                :: coord_error
    integer                         :: nnods
    
    call get_coords(uel_coords_check)
    uel_coords_check(1, :) = uel_coords_check(1, :) + coords(1,1)
    uel_coords_check(2, :) = uel_coords_check(2, :) + coords(2,1)
    nnods = size(coords,2)
    coord_error = norm(coords(1:2, 2:size(coords,2)) - uel_coords_check(1:2, :))/nnods
    
    if (coord_error > 1.e-5) then
        write(*,*) 'coordinate error = ', coord_error
        write(*,*) 'element coordinates do not match, check that uel and setup is in sync'
        call xit()
    endif
    
end subroutine

end module wheel_super_element_mod
    

subroutine uel(rhs,amatrx,svars,energy,ndofel,nrhs,nsvars,&
               props,nprops,coords,mcrd,nnode,u,du,v,a,jtype,time,dtime,&
               kstep,kinc,jelem,params,ndload,jdltyp,adlmag,predef,npredf,&
               lflags,mlvarx,ddlmag,mdload,pnewdt,jprops,njprop,period)
    use uel_mod
    use wheel_super_element_mod
    use debug_mod
    implicit none
    double precision, intent(inout) :: rhs(mlvarx,*), amatrx(ndofel,ndofel), svars(nsvars), energy(8), pnewdt
    double precision, intent(in)    :: props(*), coords(mcrd,nnode)
    double precision, intent(in)    :: u(ndofel), du(mlvarx,*), v(ndofel), a(ndofel)
    double precision, intent(in)    :: time(2), dtime, period, params(3)
    double precision, intent(in)    :: jdltyp(mdload,*), adlmag(mdload,*), ddlmag(mdload,*)
    double precision, intent(in)    :: predef(2,npredf,nnode)
    integer, intent(in)             :: ndofel, nrhs, nsvars, nprops, njprop, mcrd, nnode, jtype, kstep, kinc
    integer, intent(in)             :: jelem, ndload, mdload, npredf, jprops(*), lflags(*), mlvarx
      
    double precision, allocatable   :: Kprim(:,:)
    double precision, allocatable   :: uprim(:), Fprim(:), Fint(:)
    double precision                :: rotation
    integer                         :: k1, kmax
    
    
    allocate(Kprim(ndofel, ndofel), Fprim(ndofel), Fint(ndofel))
    
    call check_coords(coords)
    rotation = u(3)
    
    call get_unrotated_stiffness(Kprim) ! Get unrotated stiffness from static condensation
    Kprim = Kprim*props(1)              ! Scale with Elastic modulus
    
    ! Calculate right hand side
    !  Transform dof to wheel coordinate system
    call get_uprim(coords, u, uprim)    
    !  Calculate forces in wheel coordinate system
    Fprim = matmul(Kprim, uprim)
    !  Convert forces to global coordinate system
    call get_F_gcs(rotation, Fprim, Fint)
    !  Save forces to residual
    rhs(1:ndofel,1) = -Fint
    
    ! Calculate stiffness
    call rotate_stiffness(u(3), Kprim, amatrx)
    
    !call uel_output(lflags, kinc, kstep, time(2))
    
end subroutine uel