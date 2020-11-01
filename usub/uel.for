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

include 'usub_utils_mod.f90'
include 'uel_stiff_mod.f90'
include 'uel_trans_mod.f90'

subroutine uel(rhs,amatrx,svars,energy,ndofel,nrhs,nsvars,&
               props,nprops,coords,mcrd,nnode,u,du,v,a,jtype,time,dtime,&
               kstep,kinc,jelem,params,ndload,jdltyp,adlmag,predef,npredf,&
               lflags,mlvarx,ddlmag,mdload,pnewdt,jprops,njprop,period)
    use uel_stiff_mod, only : uel_stiffness, allocate_uel_stiffness
    use uel_trans_mod, only : get_u_prim, get_f_glob, get_k_glob, get_phi
    implicit none
    double precision, intent(inout) :: rhs(mlvarx,*), amatrx(ndofel,ndofel), svars(nsvars), energy(8), pnewdt
    double precision, intent(in)    :: props(*), coords(mcrd,nnode)
    double precision, intent(in)    :: u(ndofel), du(mlvarx,*), v(ndofel), a(ndofel)
    double precision, intent(in)    :: time(2), dtime, period, params(3)
    double precision, intent(in)    :: jdltyp(mdload,*), adlmag(mdload,*), ddlmag(mdload,*)
    double precision, intent(in)    :: predef(2,npredf,nnode)
    integer, intent(in)             :: ndofel, nrhs, nsvars, nprops, njprop, mcrd, nnode, jtype, kstep, kinc
    integer, intent(in)             :: jelem, ndload, mdload, npredf, jprops(*), lflags(*), mlvarx
      
    double precision, allocatable   :: u_prim(:)     ! Element displacements in unrotated coordinate system
    double precision, allocatable   :: f_prim(:)    ! Element forces in undeformed unrotated system
    double precision, allocatable   :: f_glob(:)    ! Element forces in deformed rotated system
    double precision                :: phi_rp(3)    ! Rotation of reference point around x, y, z axis
    
    allocate(f_prim(ndofel), f_glob(ndofel))
    allocate(u_prim(ndofel))
    
    if (not(allocated(uel_stiffness))) call allocate_uel_stiffness(props(1))
    
    ! Get rotation of reference point
    phi_rp = get_phi(u)
    
    ! Get displacements in unrotated coordinate system
    call get_u_prim(coords, u, u_prim)
    
    ! Get forces in unrotated coordinate system
    f_prim = matmul(uel_stiffness, u_prim)
    
    call get_f_glob(phi_rp, f_prim, f_glob)
    
    rhs(1:ndofel,1) = -f_glob
    
    ! Rotate stiffness
    call get_k_glob(phi_rp, amatrx)
    
    
end subroutine uel