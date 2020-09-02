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
module wheel_super_element_mod
implicit none

contains

subroutine get_rotation_matrix(rotation_angle, ndof, rotation_matrix)
implicit none
    double precision, intent(in)    :: rotation_angle
    integer, intent(in)             :: ndof
    double precision, allocatable   :: rotation_matrix(:,:)
    integer                         :: k1, k2
    double precision                :: rotation_sub_matrix(2,2)
    
    allocate(rotation_matrix(ndof,ndof))
    
    rotation_sub_matrix(1, :) = [cos(rotation_angle), sin(rotation_angle)]
    rotation_sub_matrix(2, :) = [-sin(rotation_angle), cos(rotation_angle)]
    
    rotation_matrix(1:2, 1:2) = rotation_sub_matrix
    do k1=1,(ndof-3)/2
        k2 = 3 + 2*k1 - 1
        rotation_matrix(k2:(k2+1), k2:(k2+1)) = rotation_sub_matrix
    enddo
    
end subroutine get_rotation_matrix

subroutine get_stiffness_matrix(ke)
implicit none
    double precision    :: ke(:,:)
    
    !<ke_to_be_defined_by_python_script>
    
end subroutine

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

end module wheel_super_element_mod
    

subroutine uel(rhs,amatrx,svars,energy,ndofel,nrhs,nsvars,&
               props,nprops,coords,mcrd,nnode,u,du,v,a,jtype,time,dtime,&
               kstep,kinc,jelem,params,ndload,jdltyp,adlmag,predef,npredf,&
               lflags,mlvarx,ddlmag,mdload,pnewdt,jprops,njprop,period)
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
      
    double precision, allocatable   :: rotation_matrix(:,:)
    double precision                :: rotation
    integer                         :: k1, kmax
!   user coding to define RHS, AMATRX, SVARS, ENERGY, and PNEWDT
    rotation = u(3)
    call get_rotation_matrix(rotation, ndofel, rotation_matrix)
    
    call get_stiffness_matrix(amatrx)
    amatrx = -amatrx
    !amatrx = props(1)*matmul(transpose(rotation_matrix), matmul(amatrx, rotation_matrix))
    rhs(:,1) = -matmul(amatrx, u)
    
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
    write(*,*) 'du:'
    write(*,*) du
    write(*,*) '--- end uel output ---'
    
end subroutine uel