!DEC$ FREEFORM
! Abaqus utility modules
!include 'abaqus_utils_mod.f90'          ! Do not include when running Abaqus
include 'abaqus_utils_dummy_mod.f90'    ! Include when running Abaqus
include 'includes.f90'


! ============================================== UEL ==============================================
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

subroutine uel(rhs,amatrx,svars,energy,ndofel,nrhs,nsvars,&
               props,nprops,coords,mcrd,nnode,u,du,v,a,jtype,time,dtime,&
               kstep,kinc,jelem,params,ndload,jdltyp,adlmag,predef,npredf,&
               lflags,mlvarx,ddlmag,mdload,pnewdt,jprops,njprop,period)
    use uel_stiff_mod, only : uel_stiffness, allocate_uel_stiffness
    use uel_trans_mod, only : get_u_prim, get_f_glob, get_k_glob, get_phi
    use node_id_mod, only: are_uel_coords_obtained, set_uel_coords
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
    if (not(are_uel_coords_obtained())) call set_uel_coords(coords)
    
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

! ============================================ URDFIL ============================================


subroutine urdfil(lstop,lovrwrt,kstep,kinc,dtime,time)
use urdfil_mod, only : get_data, get_data_first_time
use step_type_mod, only : get_step_type, get_cycle_nr, STEP_TYPE_ROLLING
use bc_mod, only : set_bc
implicit none
    ! Variables to be defined
    integer             :: lstop        ! Flag, set to 1 to stop analysis
    integer             :: lovrwrt      ! Flag, set to 1 to allow overwriting of
                                        ! results from current increment by next
    double precision    :: dtime        ! Time increment, can be updated
    ! Variables passed for information
    integer             :: kstep, kinc  ! Current step and increment, respectively
    double precision    :: time(2)      ! Time at end of increment (step, total)
    
    ! Internal variables
    integer, allocatable            :: node_n(:)            ! Contact node numbers
    double precision, allocatable   :: node_u(:,:)          ! Contact node displacements
    double precision, allocatable   :: node_c(:,:)          ! Contact node coordinates
    integer                         :: rp_n                 ! Reference point node number
    double precision                :: rp_u(3)              ! Reference point displacements
    double precision                :: angle_incr           ! Angular nodal spacing (wheel)
    integer                         :: cycle_nr             ! Rollover cycle nr
    double precision, allocatable   :: contact_node_disp(:,:,:) ! Contact node disp
    double precision, allocatable   :: wheel_rp_disp(:)     ! Wheel rp disp and rot
    double precision, allocatable   :: rail_rp_disp(:)      ! Rail rp disp and rot
    
    if (get_step_type(kstep) == STEP_TYPE_ROLLING) then
        cycle_nr = get_cycle_nr(kstep)
        if (cycle_nr == 1) then
            call get_data_first_time(kstep, kinc, contact_node_disp, wheel_rp_disp, rail_rp_disp)
        else
            call get_data(kstep, kinc, contact_node_disp, wheel_rp_disp, rail_rp_disp)
        endif
        call set_bc(contact_node_disp, wheel_rp_disp, rail_rp_disp, cycle_nr)
    endif
    
    lstop = 0   ! Continue analysis (set lstop=1 to stop analysis)
    lovrwrt = 1 ! Overwrite read results. (These results not needed later, set to 0 to keep in .fil)
    
end subroutine

! ============================================= DISP =============================================

subroutine disp(u,kstep,kinc,time,node,noel,jdof,coords)
use abaqus_utils_mod
use usub_utils_mod, only : write_node_info
use step_type_mod, only : get_step_type, get_cycle_nr, STEP_TYPE_INITIAL_DEPRESSION, &
                          STEP_TYPE_ROLLING, STEP_TYPE_MOVE_BACK, STEP_TYPE_REAPPLY_LOAD, &
                          STEP_TYPE_RELEASE_NODES
use node_id_mod, only : get_node_type, NODE_TYPE_UNKNOWN, NODE_TYPE_WHEEL_RP, NODE_TYPE_RAIL_RP, &
                        NODE_TYPE_WHEEL_CONTACT
use disp_mod, only : get_bc_rail_rp, get_bc_wheel_rp, get_bc_wheel_contact
implicit none
    ! Interface variables for disp subroutine
    double precision    :: u(3)         ! u(1) is total value of dof (except rotation where the 
                                        ! incremental value should be specified). u(2:3) are the 
                                        ! du(1)/dt and d^2u(1)/dt^2 req. only in dyn. analyses. 
    double precision    :: time(3)      ! 1: current step time, 2: current total time, 
                                        ! 3: current time increment
    double precision    :: coords(3)    ! Current coordinates at end of previous increment if nlgeom
    integer             :: kstep, kinc  ! Step and increment number
    integer             :: node, noel   ! Node (not connector) and element number (not bc)
    integer             :: jdof         ! Degree of freedom number (at node) u(1) corresponds to.
    
    ! Internal variables
    integer             :: step_type    ! 1: return step, 2: reapply_step, 3: release nodes step
                                        ! 0: rolling_step_name    
    integer             :: cycle_nr     ! The number of rollover cycles, starting at 1
    integer             :: file_id      ! File identifier for bc-file written by urdfil
    integer             :: io_status    ! Status for file to handle i/o-errors
    integer             :: node_type    ! 1: Reference point, 2: Contact node
    double precision    :: bc_val       ! Value from bc file    
    
    step_type = get_step_type(kstep)
    cycle_nr = get_cycle_nr(kstep)
    call get_node_type(node_label=node, node_coords=coords, node_type=node_type)
    
    if (node_type == NODE_TYPE_RAIL_RP) then
        call get_bc_rail_rp(step_type, cycle_nr, time, jdof, bc_val)
    elseif (node_type == NODE_TYPE_WHEEL_RP) then
        call get_bc_wheel_rp(step_type, cycle_nr, time, jdof, bc_val)
    elseif (node_type == NODE_TYPE_WHEEL_CONTACT) then
        call get_bc_wheel_contact(step_type, cycle_nr, node, jdof, bc_val)
    else
        write(*,*) 'Did not expect call to disp for this node:'
        call write_node_info(node, coords, jdof, kstep, kinc)
        call xit()
    endif
    
    ! Check for nan-values
    if (bc_val /= bc_val) then  
        write(*,*) 'NaN boundary condition calculated for'
        call write_node_info(node, coords, jdof, kstep, kinc)
        call xit()
    endif
    
    u(1) = bc_val
        
end subroutine