# User subroutine

Questions that needs to be solved

* Need to connect element dofs to node labels/mesh_inds
* Would be good to only read node coordinates the first time, then these can be saved and we have the initial values always to work with.
* Should add `wheel_contact_node_coords` and `wheel_contact_node_edofs` to `node_id_mod` . We can use the coordinates to match the dof numbers. 

## Overall working

When referring to `DISP` this also includes `disp_mod`, similar for `URDFIL` and `urdfil_mod`. `DISP` relies on `step_type_mod` to obtain the step type.

1. Initial depression step
   - [x] `UEL` gives its nodal coordinates to `node_id_mod` the first time it is called 
   - [x] `DISP` asks `node_id_mod` for the node type. It is not setup, but this is then done for the reference points. At this point `DISP` should not be called for contact nodes.
   - [x] `DISP` asks `load_param_mod`  to read the load parameters from the file `load_param.txt`(see below). It also sets up the initial rolling parameters. 
   - [x] `DISP` asks `load_param_mod` for bc for the wheel rp
2. Rolling step (cycle 0) **Must check that cycle numbering is correctly implemented, unsure about that**
   - [x] `DISP` asks `load_param_mod` for bc for the wheel rp
   - At the end of the rolling step:
     * [x] `URDFIL` reads the `.fil` file 
     * [x] The first time, `URDFIL` asks `node_id_mod` to setup the mesh info to structure the node label information, node coordinates and node dofs. 
     * [x] `URDFIL` calls `bc_mod` to calculate the new boundary conditions, with the help of `node_id_mod` and `uel_stiffness_mod`
     * [x] `bc_mod` asks `load_param_mod` to save the  boundary conditions and update the current parameters. 
3. Moving back step (cycle 1)
   - [x] `DISP` asks `load_param_mod` for boundary conditions for wheel rp and wheel contact nodes
4. Reapply load step (cycle 1)
   - [ ] `DISP` asks `load_param_mod` for boundary conditions for wheel rp and wheel contact nodes (***Needed?***)
5. Release nodes step (cycle 1)
   - [ ] `DISP` asks `load_param_mod` for boundary conditions for wheel rp and wheel contact nodes (***Needed?***)
6. Rolling step (cycle 1): Continue iterating, but now it is not necessary to setup the mesh info at the end of the rolling step. 
## Module descriptions

The main file is the `usub_3d.for`, containing the Abaqus user subroutines `UEL`, `URDFIL`, and `DISP`.  These use the following modules

### `load_param_mod`
Is used to save the load parameters. Used by the `disp` subroutine to read the boundary conditions to apply. Also, some parameters read by `bc_mod` to calculate the boundary conditions
### `bc_mod`
Used to calculate the boundary conditions and save them to `load_param_mod`. 
### `node_id_mod`
Used to determine node type and organize node positions using an index matrix where indices go in the angular and across directions. 

### `abaqus_utils_mod`

Contained in two files: `abaqus_utils_mod.f90` and `abaqus_utils_dummy_mod`. The latter contains only an empty module and should be included when compiling with Abaqus. The former should contain subroutines normally provided by Abaqus to allow compilation outside the Abaqus environment. This allows testing of the subroutines. 

### `disp_mod`

Provides functions to get the boundary conditions from `load_param_mod`

### `filenames_mod`

Contains the names of the files used to read in information in the beginning of the simulation

### `step_type_mod`

Contains information and routines for obtaining the type of step and cycle number based in the step number (kstep)

### `uel_stiff_mod`

Contains the unrotated element stiffness and subroutine to read this from file in beginning of simulation

### `uel_trans_mod`

Contains routines for transforming the element stiffness matrix and calculating the element force vectors

### `urdfil_mod`

Contains subroutines for reading from the result file and give that information to

- `node_id_mod` (First time we read data)
- `bc_mod` (Each time, so that it can calculate the updated boundary conditions)

### `usub_utils_mod`

Collection of convenience routines when using subroutines in general. 

### External module dependency

In addition to the modules mentioned above, the following modules from the `fortran-utilities` repository are used:

- `find_mod`: Module containing a function for finding a the index of a match in arrays
- `sort_mod`: Module for sorting arrays or getting the indices to sort them
- `resize_array_mod`: Module for resizing (expanding or contracting) arrays
- `linalg_mod`: Module for linear algebra, currently only a norm function. 

## Files required for user subroutines

### `load_param.txt`

Should specify the loading parameters, and have the following format

1. `rail_length`
2. `initial_depression_speed`
3. `number_specified_cycles`
4. `cycle_nr`,  `rolling_time`, `rot_per_length`, `rail_extension`
5. `cycle_nr`,  `rolling_time`, `rot_per_length`, `rail_extension`
6. ...

Here, `rail_length` is the length of the rail. `initial_depression_speed` is the speed at which the wheel is lowered in the first step, before changing to load control. (It is just more convenient to specify the speed, as then it is not needed to specify both the time to perform the initial depression and the total amount). `number_specified_cycles` says how many more lines to read after its line. On the remaining lines, the following parameters are specified:

* `cycle_nr`
  The cycle number from which the present line's specification will be applied. On the first line, this must be 1
* `rolling_time`
  The duration of the rolling step. Note that this must match the value given in the step definition in Abaqus
* `rot_per_length`
  The amount to rotate for the given rolling length (i.e. it has unit rad/mm)
* `rail_extension`
  The length with which the rail is extended from its initial length during the cycle. Gives the total extension, and is applied as a linear ramp to the given value. 

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

