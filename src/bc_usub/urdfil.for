!Important links:
!https://help.3ds.com/2017/English/DSSIMULIA_Established/SIMACAEOUTRefMap/simaout-c-recordswrittenforanynodefileoutputrequest.htm?ContextScope=all&id=94692c57a5174ef6a21cf2acb2e78e69#Pg0
!https://help.3ds.com/2017/English/DSSIMULIA_Established/SIMACAEKEYRefMap/simakey-r-nodefile.htm?ContextScope=all#simakey-r-nodefile
!https://help.3ds.com/2017/English/DSSIMULIA_Established/SIMACAEOUTRefMap/simaout-c-stdoutputvar.htm?ContextScope=all
!https://help.3ds.com/2017/English/DSSIMULIA_Established/SIMACAEOUTRefMap/simaout-c-format.htm?ContextScope=all#simaout-c-format
!https://help.3ds.com/2017/English/DSSIMULIA_Established/SIMACAESUBRefMap/simasub-c-urdfil.htm?ContextScope=all
!DEC$ FREEFORM

module urdfil_mod
implicit none
    integer, parameter  :: NPRECD = 2           ! Precision for floats
    integer, parameter  :: GUESS_NUM = 1000     ! Guess for number of info items
    contains
    
    subroutine read_node_disps(nodes_u, nodes_num)
    implicit none
        ! Output
        double precision, allocatable   :: nodes_u(:,:) ! Node displacements
        integer, allocatable            :: nodes_num(:) ! Node numbers
        ! Variables for reading .fil files
        double precision    :: array(513)       ! Array to save float information to
        integer             :: int_array(NPRECD,513)    ! Array to save int info to
        integer             :: fil_status       ! Status for .fil file input/output
        integer             :: record_length    ! Variable to store the length of the current record
        integer             :: record_type_key  ! Variable to store the type of the current record
        ! Other internal variables
        double precision, allocatable   :: nodes_u_tmp(:,:) ! Node displacements
        integer, allocatable            :: nodes_num_tmp(:) ! Node numbers
        integer                         :: k1               ! Counter
        
        
        k1 = 0
        do while (.true.)
            call dbfile(0, array, fil_status)
            if (fil_status .ne. 0) exit
            record_length = transfer(array(1), 1)
            record_type_key = transfer(array(2), 1)
            if (record_type_key==101) then  ! Node displacement information
                ! If first iteration, allocate tmp variables
                if (k1 == 0) then 
                    allocate(nodes_u_tmp(record_length - 3, GUESS_NUM))
                    allocate(nodes_num_tmp(GUESS_NUM))
                endif
                
                k1 = k1 + 1
                ! Change size if necessary
                if (k1 > size(nodes_num_tmp)) then
                    allocate(nodes_u, source=nodes_u_tmp)
                    allocate(nodes_num, source=nodes_num_tmp)
                    deallocate(nodes_u_tmp, nodes_num_tmp)
                    allocate(nodes_u_tmp(size(nodes_u, 1), 2*k1))
                    allocate(nodes_num_tmp(2*k1))
                    nodes_u_tmp(:, 1:(k1-1)) = nodes_u
                    nodes_num_tmp(1:(k1-1)) = nodes_num
                    deallocate(nodes_u, nodes_num)
                endif
                nodes_num_tmp(k1) = transfer(array(3), 1)
                nodes_u_tmp(:, k1) = array(4:record_length)
            endif
            
        enddo
        allocate(nodes_u, source=nodes_u_tmp(:, 1:k1))
        allocate(nodes_num, source=nodes_num_tmp(1:k1))
        
    end subroutine 
 
end module urdfil_mod

SUBROUTINE URDFIL(lstop,lovrwrt,kstep,kinc,dtime,time)
use urdfil_mod
implicit none
!    integer, parameter  :: NPRECD = 2   ! Precision for floats
    ! Variables to be defined
    integer             :: lstop        ! Flag, set to 1 to stop analysis
    integer             :: lovrwrt      ! Flag, set to 1 to allow overwriting of
                                        ! results from current increment by next
    double precision    :: dtime        ! Time increment, can be updated
    ! Variables passed for information
    integer             :: kstep, kinc  ! Current step and increment, respectively
    double precision    :: time(2)      ! Time at end of increment (step, total)
    ! Internal variables
    double precision    :: array(513)       ! Array to save float information to
    integer             :: int_array(NPRECD,513)    ! Array to save int info to
    integer             :: fil_status       ! Status for .fil file input/output
    integer             :: record_length    ! Variable to store the length of the current record
    integer             :: record_type_key  ! Variable to store the type of the current record
    ! New variables
    double precision, allocatable   :: nodes_u(:,:)
    integer, allocatable            :: nodes_num(:)
    integer                         :: k1
    integer                         :: file_id, cwd_length
    CHARACTER(len=255)              :: cwd
    
    ! Use Abaqus utility routine, getoutdir, to get the output directory of the current job
    ! Otherwise, a special temporary folder will contain all the files making it difficult to debug.
    call getoutdir(cwd, cwd_length)
    
    file_id = 101
    
    array = -1.d0
    
    ! Set position to current increment and step
    CALL POSFIL(kstep,kinc,array,fil_status)
    
    ! Read nodal displacements
    call read_node_disps(nodes_u, nodes_num)
    
    !open(file_id,file='nodal_output.txt', action='write', status='replace')
    open(file_id, file=trim(cwd)//'/nodal_output.txt')
    write(file_id,"(A, I, A, I)") 'Size of nodes_u: ', size(nodes_u, 1), ' x ', size(nodes_u,2)
    write(file_id,"(A4, A25, A25)") 'NUM', 'U1', 'U2'
    do k1=1,size(nodes_num)
        write(file_id,"(I4, E25.15, E25.15)") nodes_num(k1), nodes_u(1,k1), nodes_u(2,k1)
    enddo
    close(file_id)
    
    LOVRWRT = 1 ! Can delete contents of .fil file now, no need for these results anymore. 
    
END