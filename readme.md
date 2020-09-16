[//]: # "To preview markdown file in Emacs type C-c C-c p"

# Abaqus Rollover Simulation
Script to setup rollover simulation in Abaqus for CHARMEC

## Contributors
* Knut Andreas Meyer 
* Rostyslav Skrypnyk

## Running for the first time 
### Requirements
* Abaqus Standard setup to compile fortran user subroutines
* Abaqus environment file setup to look for user subroutines in the current working directory (this can be done by editing/making `abaqus_v6.env` and adding the line `usub_lib_dir="<path_to_working_directory>"`)

### Steps
1. Create a new file in the `src/` directory named `user_settings.py` and copy the contents from `user_settings_example.py`
2. Run the python script `src/wheel_super_element/create_super_wheel.py` from a directory in which you wish to save the wheel super element
3. This will create files `uel.for`, `uel_coords.npy` and `uel_info.json` in the folder from which you called `create_super_wheel.py`
5. Edit `user_settings.py` to update `super_element_path` to the folder containing the `uel.for`/`uel.f` that you created previously. 
6. Run `src/rollover_model.py` from Abaqus

## Using material subroutines

To use a material subroutine see the material `chaboche_umat` in `user_settings_example.py` for inspiration. The field `'material_model'` must be set to  `'user'` and the field `'mpar'` must contain a dictionary with the following fields:

* `'nstatv'`: Give an int for how many state variables the material model requires
* `'src_folder'`: Give the path to the folder containing a file named `umat.for`/`umat.f`. The folder must contain all required files such that calling `abaqus make library=umat.for` (or `umat.f` ) would work in that folder (This will not be done however, the content will be copied)
* `'user_mpar_array'`: A tuple containing the material parameter that should be supplied to the user material routine

