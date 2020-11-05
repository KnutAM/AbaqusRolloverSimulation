# User subroutine

Questions that needs to be solved

* Need to connect element dofs to node labels/mesh_inds
* Would be good to only read node coordinates the first time, then these can be saved and we have the initial values always to work with.
* Should add `wheel_contact_node_coords` and `wheel_contact_node_edofs` to `node_id_mod` . We can use the coordinates to match the dof numbers. 

## Overall working

When referring to `DISP` this also includes `disp_mod`, similar for `URDFIL` and `urdfil_mod`. `DISP` relies on `step_type_mod` to obtain the step type.

1. Initial depression step
   - `UEL` gives its nodal coordinates to `node_id_mod` the first time it is called
   - `DISP` asks `node_id_mod` for the node type. It is not setup, but this is then done for the reference points.
   - `DISP` asks `load_param_mod`  to read the load parameters from the file `load_param.txt`(see below)
   - `DISP` asks `load_param_mod` for bc for the wheel rp
2. Rolling step (cycle 0) **Must check that cycle numbering is correctly implemented, unsure about that**
   - `DISP` asks `load_param_mod` for bc for the wheel rp
   - At the end of the rolling step:
     * `URDFIL` reads the `.fil` file 
     * The first time, `URDFIL` asks `node_id_mod` to setup the mesh info to structure the node label information, node coordinates and node dofs. 
     * `URDFIL` calls `bc_mod` to calculate the new boundary conditions, with the help of `node_id_mod` and `uel_stiffness_mod`
     * `bc_mod` asks `load_param_mod` to save the  boundary conditions
3. Moving back step (cycle 1)
   - `DISP` asks `load_param_mod` for boundary conditions for wheel rp and wheel contact nodes
4. Reapply load step (cycle 1)
   - `DISP` asks `load_param_mod` for boundary conditions for wheel rp and wheel contact nodes
5. Release nodes step (cycle 1)
   - `DISP` asks `load_param_mod` for boundary conditions for wheel rp and wheel contact nodes
6. Rolling step (cycle 1): Continue iterating, but now it is not necessary to setup the mesh info at the end of the rolling step. 
## Files required for user subroutines

### `load_param.txt`

Should specify the loading parameters, and have the following format

1. `rail_length`
2. `initial_depression_speed`
3. `number_specified_cycles`
4. `cycle_nr`,  `rolling_time`, `rot_per_length`
5. `cycle_nr`,  `rolling_time`, `rot_per_length`
6. ...

Here, `rail_length` is the length of the rail. `initial_depression_speed` is the speed at which the wheel is lowered in the first step, before changing to load control. (It is just more convenient to specify the speed, as then it is not needed to specify both the time to perform the initial depression and the total amount). `number_specified_cycles` says how many more lines to read after its line. On the remaining lines, the following parameters are specified:

* `cycle_nr`
  The cycle number from which the present line's specification will be applied. On the first line, this must be 1
* `rolling_time`
  The duration of the rolling step. Note that this must match the value given in the step definition in Abaqus
* `rot_per_length`
  The amount to rotate for the given rolling length (i.e. it has unit rad/mm)

The settings are applied from the given `cycle_nr` until a new `cycle_nr` is given. 

### `uel_stiffness.txt`

The first line gives the number of degrees of freedom, `ndof`

Line `2` to `ndof+1` gives the stiffness matrix' first column

Line `ndof+2` to `2*ndof` gives the stiffness matrix' second column, excluding the first row

Line `2*ndof+1` to `3*ndof-2` gives the stiffness matrix' third column, excluding the two first rows

And so on until the entire lower diagonal (including the diagonal) has been specified. The matrix is assumed to be symmetric. 

### `rp_coord.txt`

Each line give the x, y, z coordinates of the reference points:

1. Wheel reference point
2. Rail reference point

### ``

### ``

